from api import Api
from inventory import Inventory

import json
import os.path
import datetime
from pprint import pprint
from pickle import Pickler, Unpickler
from time import sleep
from threading import Thread, Lock

def setup():
  global api, cfg, inventory, inventoryLock, playerHistory
  with open(os.path.expanduser("~/.ingressbot.pwd"), "rb") as f:
    pwd = json.load(f)
    userEmail = pwd["userEmail"]
    userPassword = pwd["userPassword"]
  with open(os.path.expanduser("~/.ingressbot.cfg"), "rb") as f:
    cfg = json.load(f)
  api = Api(userEmail, userPassword)
  try:
    with open(os.path.expanduser("~/.ingressbot.pkl"), "rb") as f:
      unpickler = Unpickler(f)
      inventory = unpickler.load()
  except:
    inventory = Inventory()
  inventoryLock = Lock()
  playerHistory = dict()
  
def cleanup():
  try:
    inventoryLock.acquire()
    with open(os.path.expanduser("~/.ingressbot.pkl"), "wb") as f:
      pickler = Pickler(f)
      pickler.dump(inventory)
  finally:
    inventoryLock.release()
          
def main():
  threads = []
  threads.append(Thread(target=refreshInventory))
  threads.append(Thread(target=refreshChat))
  for t in threads:
    t.start()

def processCommand(sender, message):
  if(sender != api.playerGUID or not message.startswith('!')):
    return
  tokens = message.split(' ')
  if(len(tokens) == 0):
    return
  if(tokens[0] == "!helo"):
    api.say("Hello World", True)
  elif(tokens[0] == "!stat"):
    if(len(tokens) == 1):
      inventoryLock.acquire()
      lines = inventory.statsToStrings()
      inventoryLock.release()
      for line in lines:
        api.say(line)
    elif(len(tokens) == 2 and ((tokens[1] == "rst") or (tokens[1] == "reset"))):
      inventoryLock.acquire()
      inventory.resetStats()
      inventoryLock.release()
      api.say("Stats resetted")
  elif(tokens[0] == "!seen"):
    if(len(tokens) == 2):
      player = tokens[1].lower()
      if player in playerHistory:
        entry = playerHistory[player]
        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(entry["when"] / 1000.0)
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        deltaStr = ""
        if(delta.days > 0):
          deltaStr += str(delta.days) + "d "
        if(hours > 0):
          deltaStr += str(hours) + "h "
        deltaStr += str(minutes) + "m"
        api.say(player + " was last seen " + deltaStr + " ago on " + entry["where"])
      else:
        api.say("Can't remember " + player)
        
      
def trackPlayers(result):
  for message in result:
    plext = message[2]["plext"]
    if plext["plextType"] == "SYSTEM_BROADCAST":
      markups = plext["markup"]
      if "team" in markups[0][1]:
        player = markups[0][1]["plain"].encode("utf-8").lower()
        team = markups[0][1]["team"].encode("utf-8")
        timestamp = long(message[1])
        portal = None
        for markup in markups:
          if markup[0] == "PORTAL":
            portal = markup[1]["name"].encode("utf-8")
            break
        if portal != None:
          if player in playerHistory:
            entry = playerHistory[player]
          else:
            entry = {"when" : long(-1), "where" : ""}
            playerHistory[player] = entry
          if(entry["when"] < timestamp):
            entry["when"] = timestamp
            entry["where"] = portal
  
def refreshInventory():
  while True:
    result = api.getInventory(inventory.lastQueryTimestamp);
    if("gameBasket" in result):
      try:
        inventoryLock.acquire()
        inventory.processGameBasket(result)
      finally:
        inventoryLock.release()
    sleep(10)
    
def chatLookback(desiredMinTs, initialMaxTs):
  maxTs = long(initialMaxTs)
  while (maxTs > long(desiredMinTs)):
    result = api.getMessages(cfg["bounds"], desiredMinTs, maxTs, 100, False)["result"]
    trackPlayers(result)
    if(len(result) == 0):
      break
    lowestTs = maxTs
    for message in result:
      lowestTs = min(long(message[1]), lowestTs)
    if(maxTs == lowestTs):
      break
    maxTs = lowestTs

def refreshChat():
  result = api.getMessages(cfg["bounds"], -1, -1, 1, False)["result"]
  lastTimestamp = result[0][1]
  Thread(target=chatLookback, args=(long(lastTimestamp)-(long(cfg["chatLookbackHours"])*3600000), lastTimestamp)).start()
  
  lastMessages = set()
  for message in result:
    lastMessages.add(message[0])
  while True:
    response = api.getMessages(cfg["bounds"], lastTimestamp, -1, 100, False)
    if "result" in response:
      result = response["result"]
      trackPlayers(result)
      if(len(result) > 0):
        lastTimestamp = result[0][1]
      thisMessages = set()
      for message in result:
        thisMessages.add(message[0])
        if(not message[0] in lastMessages):
          plext = message[2]["plext"]
          sender = None
          text = None
          for markup in plext["markup"]:
            if(markup[0] == "TEXT"):
              text = markup[1]["plain"].encode("utf-8")
            elif(markup[0] == "SENDER"):
              sender = markup[1]["guid"].encode("utf-8")
          if(sender is not None and text is not None):
            processCommand(sender, text)
      lastMessages = thisMessages
      sleep(5)
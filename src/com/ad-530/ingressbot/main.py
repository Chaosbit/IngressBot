#!/usr/bin/python

from api import Api
from inventory import Inventory

import json
import os.path
from pprint import pprint
from pickle import Pickler, Unpickler
from time import sleep
from threading import Thread, Lock

try:
  with open(os.path.expanduser("~/.ingressbot.pwd"), "rb") as f:
    pwd = json.load(f)
    userEmail = pwd["userEmail"]
    userPassword = pwd["userPassword"]
except:
###################### Ausfuellen ################################
  userEmail    = ""
  userPassword = ""
#################################################################

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
  
def refreshInventory():
  while True:
    lastTs = inventory.lastQueryTimestamp
    result = api.getInventory(lastTs);
    if("gameBasket" in result):
      try:
        inventoryLock.acquire()
        inventory.processGameBasket(result)
        if(lastTs <= 0):
          inventory.resetStats()
        with open(os.path.expanduser("~/.ingressbot.pkl"), "wb") as f:
          pickler = Pickler(f)
          pickler.dump(inventory)
      finally:
        inventoryLock.release()
    sleep(10)
  
def refreshChat():
  result = api.getMessages(cfg["bounds"], -1, 1, False)["result"]
  lastTimestamp = result[0][1]
  lastMessages = set()
  for message in result:
    lastMessages.add(message[0])
  while True:
    result = api.getMessages(cfg["bounds"], lastTimestamp, 100, False)["result"]
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
    
    
threads = []
threads.append(Thread(target=refreshInventory))
threads.append(Thread(target=refreshChat))
for t in threads:
  t.start()
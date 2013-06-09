from api import Api
from inventory import Inventory

import json
import os.path
import datetime
from pickle import Pickler, Unpickler
from threading import Lock, Thread
from Thread import TimerThread
import logging

class Ingressbot(object):

  def __init__(self):
    self.stdin_path = '/dev/null'
    self.stdout_path = '/dev/null'
    self.stderr_path = '/dev/null'
    self.pidfile_path =  '/var/lock/ingressbot.pid'
    self.pidfile_timeout = 5
    self.logger = logging.getLogger("ingressbot")
    
    self.inventory = Inventory()
    self.inventoryLock = Lock()
    self.playerHistory = dict()
    self.threads = []
    
  def run(self):
    with open(os.path.expanduser("~/.ingressbot.pwd"), "rb") as f:
      pwd = json.load(f)
      userEmail = pwd["userEmail"]
      userPassword = pwd["userPassword"]
    with open(os.path.expanduser("~/.ingressbot.cfg"), "rb") as f:
      self.cfg = json.load(f)
      
    self.api = Api(userEmail, userPassword)
    try:
      with open(os.path.expanduser("~/.ingressbot.pkl"), "rb") as f:
        unpickler = Unpickler(f)
        self.inventory = unpickler.load()
    except:
      pass
    
    try:
      self.threads.append(TimerThread(interval=10, target=self.refreshInventory))
      self.threads.append(TimerThread(interval=5, setup=self.setupRefreshChat, target=self.refreshChat))
      for t in self.threads:
        t.start()
      self.logger.info("started")
      for t in self.threads:
        while t.is_alive():
          t.join(timeout=3600.0)
    except Exception as e:
      self.logger.critical("ex: " + str(type(e)) + ": " + e.message)
    
  def stop(self):
    try:
      for t in self.threads:
        try:
          t.interrupt()
        except Exception as e:
          self.logger.critical("ex: " + str(type(e)) + ": " + e.message)
      for t in self.threads:
        try:
          t.join()
        except Exception as e:
          self.logger.critical("ex: " + str(type(e)) + ": " + e.message)
      self.inventoryLock.acquire()
      with open(os.path.expanduser("~/.ingressbot.pkl"), "wb") as f:
        pickler = Pickler(f)
        pickler.dump(self.inventory)
    finally:
      self.inventoryLock.release()
    self.logger.critical("stopped")

  def refreshInventory(self):
    result = self.api.getInventory(self.inventory.lastQueryTimestamp);
    if("gameBasket" in result):
      try:
        self.inventoryLock.acquire()
        self.inventory.processGameBasket(result)
      finally:
        self.inventoryLock.release()
        
  def setupRefreshChat(self):
    result = self.api.getMessages(self.cfg["bounds"], -1, -1, 1, False)["result"]
    self.lastChatTimestamp = result[0][1]
    Thread(target=self.chatLookback, args=(long(self.lastChatTimestamp)-(long(self.cfg["chatLookbackHours"])*3600000), self.lastChatTimestamp)).start()

    self.lastMessages = set()
    for message in result:
      self.lastMessages.add(message[0])

  def refreshChat(self):
    response = self.api.getMessages(self.cfg["bounds"], self.lastChatTimestamp, -1, 100, False)
    if "result" in response:
      result = response["result"]
      self.trackPlayers(result)
      if(len(result) > 0):
        self.lastChatTimestamp = result[0][1]
      thisMessages = set()
      for message in result:
        thisMessages.add(message[0])
        if(not message[0] in self.lastMessages):
          plext = message[2]["plext"]
          sender = None
          text = None
          for markup in plext["markup"]:
            if(markup[0] == "TEXT"):
              text = markup[1]["plain"].encode("utf-8")
            elif(markup[0] == "SENDER"):
              sender = markup[1]["guid"].encode("utf-8")
          if(sender is not None and text is not None):
            self.processCommand(sender, text)
      self.lastMessages = thisMessages
      
  def chatLookback(self, desiredMinTs, initialMaxTs):
    maxTs = long(initialMaxTs)
    while (maxTs > long(desiredMinTs)):
      result = self.api.getMessages(self.cfg["bounds"], desiredMinTs, maxTs, 100, False)["result"]
      self.trackPlayers(result)
      if(len(result) == 0):
        break
      lowestTs = maxTs
      for message in result:
        lowestTs = min(long(message[1]), lowestTs)
      if(maxTs == lowestTs):
        break
      maxTs = lowestTs
      
  def processCommand(self, sender, message):
    if(sender != self.api.playerGUID or not message.startswith('!')):
      return
    tokens = message.split(' ')
    if(len(tokens) == 0):
      return
    if(tokens[0] == "!helo"):
      self.api.say("Hello World", True)
    elif(tokens[0] == "!stat"):
      if(len(tokens) == 1):
        self.inventoryLock.acquire()
        lines = self.inventory.statsToStrings()
        self.inventoryLock.release()
        for line in lines:
          self.api.say(line)
      elif(len(tokens) == 2 and ((tokens[1] == "rst") or (tokens[1] == "reset"))):
        self.inventoryLock.acquire()
        self.inventory.resetStats()
        self.inventoryLock.release()
        self.api.say("Stats resetted")
    elif(tokens[0] == "!seen"):
      if(len(tokens) == 2):
        player = tokens[1].lower()
        if player in self.playerHistory:
          entry = self.playerHistory[player]
          delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(entry["when"] / 1000.0)
          hours, remainder = divmod(delta.seconds, 3600)
          minutes, seconds = divmod(remainder, 60)
          deltaStr = ""
          if(delta.days > 0):
            deltaStr += str(delta.days) + "d "
          if(hours > 0):
            deltaStr += str(hours) + "h "
          deltaStr += str(minutes) + "m"
          self.api.say(player + " was last seen " + deltaStr + " ago on " + entry["where"])
        else:
          self.api.say("Can't remember " + player)

  def trackPlayers(self, result):
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
            if player in self.playerHistory:
              entry = self.playerHistory[player]
            else:
              entry = {"when" : long(-1), "where" : ""}
              self.playerHistory[player] = entry
            if(entry["when"] < timestamp):
              entry["when"] = timestamp
              entry["where"] = portal
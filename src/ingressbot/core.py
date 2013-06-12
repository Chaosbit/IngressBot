from api import Api
from inventory import Inventory, Shield, FlipCard

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
    except Exception as e:
      self.logger.critical("ex: " + str(type(e)) + ": " + e.message)
    finally:
      self.inventoryLock.release()
    self.logger.info("stopped")

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
      if(len(result) == 0): return
      self.lastChatTimestamp = result[0][1]
      thisMessages = set()
      for message in result:
        thisMessages.add(message[0])
        if(not message[0] in self.lastMessages):
          plext = message[2]["plext"]
          if plext["plextType"] == "SYSTEM_BROADCAST" or plext["plextType"] == "SYSTEM_NARROWCAST":
            self.trackPlayers(plext, long(message[1]))
          elif plext["plextType"] == "PLAYER_GENERATED":
            if plext["markup"][0][0] == "SECURE":
              sender = None
              text = None
              for markup in plext["markup"]:
                if(markup[0] == "TEXT"):
                  text = markup[1]["plain"].encode("utf-8")
                elif(markup[0] == "SENDER"):
                  sender = markup[1]["guid"].encode("utf-8")
              if(sender is not None and text is not None and text.startswith("!")):
                self.processCommand(sender, text)
      self.lastMessages = thisMessages
      
  def chatLookback(self, desiredMinTs, initialMaxTs):
    maxTs = long(initialMaxTs)
    while (maxTs > long(desiredMinTs)):
      response = self.api.getMessages(self.cfg["bounds"], desiredMinTs, maxTs, 100, False)
      if "result" in response:
        result = response["result"]
        if(len(result) == 0):
          break
        lowestTs = maxTs
        for message in result:
          lowestTs = min(long(message[1]), lowestTs)
          plext = message[2]["plext"]
          if plext["plextType"] == "SYSTEM_BROADCAST" or plext["plextType"] == "SYSTEM_NARROWCAST":
            self.trackPlayers(plext, long(message[1]))
        if(maxTs == lowestTs):
          break
        maxTs = lowestTs
      
  def processCommand(self, sender, message):
    if not message.startswith('!'): return
    tokens = message.split(' ')
    if(len(tokens) == 0):
      return
    
    if(tokens[0] == "!helo"):
      self.api.say("Hello World", True)
    elif(tokens[0] == "!stat"):
      if sender != self.api.playerGUID: return
      if(len(tokens) == 1):
        self.inventoryLock.acquire()
        lines = self.statsToStrings()
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

  def trackPlayers(self, plext, timestamp):
    markups = plext["markup"]
    player = None
    portal = None
    for markup in markups:
      if player is None and markup[0] == "PLAYER":
        player = markup[1]["plain"].encode("utf-8")
      elif portal is None and markup[0] == "PORTAL":
        portal = markup[1]["name"].encode("utf-8")
    if player is not None and portal is not None:
      key = player.lower()
      if key in self.playerHistory:
        entry = self.playerHistory[key]
      else:
        entry = {"when" : long(-1), "where" : ""}
        self.playerHistory[key] = entry
      if(entry["when"] < timestamp):
        entry["when"] = timestamp
        entry["where"] = portal
        
  def statsToStrings(self):
    lines =  []
    delta = datetime.datetime.now() - self.inventory.stats["startTime"]
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    deltaStr = ""
    if(delta.days > 0):
      deltaStr += str(delta.days) + "d "
    if(hours > 0):
      deltaStr += str(hours) + "h "
    deltaStr += str(minutes) + "m"
    lines.append("Stats since " + self.inventory.stats["startTime"].strftime("%a, %d. %b %Y %H:%M") + " (" + deltaStr + " ago)")

    line = ""
    for l in range(1, 9):
      bursters = self.inventory.stats["bursters"][l]
      if(bursters["+"] != 0 or bursters["-"] != 0):
        line += "L" + str(l) + "(+" + str(bursters["+"]) + ",-" + str(bursters["-"]) + ") "
    if(len(line) > 0):
      lines.append("B: " + line)

    line = ""
    for l in range(1, 9):
      resos = self.inventory.stats["resos"][l]
      if(resos["+"] != 0 or resos["-"] != 0):
        line += "L" + str(l) + "(+" + str(resos["+"]) + ",-" + str(resos["-"]) + ") "
    if(len(line) > 0):
      lines.append("R: " + line)

    line = ""
    for l in range(1, 9):
      cubes = self.inventory.stats["cubes"][l]
      if(cubes["+"] != 0 or cubes["-"] != 0):
        line += "L" + str(l) + "(+" + str(cubes["+"]) + ",-" + str(cubes["-"]) + ") "
    if(len(line) > 0):
      lines.append("C: " + line)
    line = ""
    shields = self.inventory.stats["shields"][Shield.COMMON]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "C (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    shields = self.inventory.stats["shields"][Shield.RARE]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "R (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    shields = self.inventory.stats["shields"][Shield.VERY_RARE]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "VR (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    if(len(line) > 0):
      lines.append("S: " + line)

    line = ""
    flipcards = self.inventory.stats["flipcards"][FlipCard.ADA]
    if(flipcards["+"] != 0 or flipcards["-"] != 0):
      line += "A (+" + str(flipcards["+"]) + ",-" + str(flipcards["-"]) + ") "
    flipcards = self.inventory.stats["flipcards"][FlipCard.JARVIS]
    if(flipcards["+"] != 0 or flipcards["-"] != 0):
      line += "J (+" + str(flipcards["+"]) + ",-" + str(flipcards["-"]) + ") "
    if(len(line) > 0):
      lines.append("F: " + line)

    if(len(lines) == 1):
      lines.append("Nothing happened")
    return lines
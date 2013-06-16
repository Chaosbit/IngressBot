#!/usr/bin/python
import daemon.runner
import datetime
from jabberbot import JabberBot, botcmd
import json
import logging
import logging.handlers
import os.path
import signal
import sys
from threading import Lock, Thread
import traceback

from api import Api
from inventory import Inventory, PortalMod, Shield, FlipCard
from Thread import TimerThread

class Ingressbot(JabberBot):

  def __init__(self, pwd, cfg):
    super(Ingressbot, self).__init__(username=pwd["jabber"]["user"], password=pwd["jabber"]["password"], acceptownmsgs=True, command_prefix=".")
    self.pwd = pwd
    self.cfg = cfg
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
    self.lastChatTimestamp = -1
    self.log.addHandler(logging.StreamHandler())
    self.log.setLevel(logging.INFO)
    
  def run(self):
    self.api = Api(self.pwd["ingress"]["userEmail"], self.pwd["ingress"]["userPassword"])
    try:
      with open(os.path.expanduser("~/.ingressbot.pkl"), "rb") as f:
        unpickler = Unpickler(f)
        self.inventory = unpickler.load()
    except:
      pass
    
    self.threads.append(TimerThread(interval=10, target=self.refreshInventory))
    self.threads.append(TimerThread(interval=10, setup=self.setupRefreshChat, target=self.refreshChat))
    self.threads.append(Thread(target=self.serve_forever))
    self.send(self.cfg["master"], "IngressBot is up and running")
    for t in self.threads:
      t.start()
    for t in self.threads:
      while t.is_alive():
        t.join(timeout=3600.0)

  
  def callback_presence(self, conn, presence):
    presence.getFrom().setResource(None)
    return super(Ingressbot, self).callback_presence(conn, presence)
    
  def callback_message(self, conn, message):
    message.getFrom().setResource(None)
    return super(Ingressbot, self).callback_message(conn, message)
    
  def stop(self):
    try:
      for t in self.threads:
        try:
          t.interrupt()
        except:
          pass
      for t in self.threads:
        try:
          t.join()
        except:
          pass
      self.inventoryLock.acquire()
      with open(os.path.expanduser("~/.ingressbot.pkl"), "wb") as f:
        pickler = Pickler(f)
        pickler.dump(self.inventory)
    finally:
      self.inventoryLock.release()
    self.logger.info("stopped")

  def refreshInventory(self):
    try:
      result = self.api.getInventory(self.inventory.lastQueryTimestamp);
      if("gameBasket" in result):
        try:
          self.inventoryLock.acquire()
          self.inventory.processGameBasket(result)
        finally:
          self.inventoryLock.release()
    except Exception as e:
      self.logger.critical("Exception: " + str(type(e)) + ": " + e.message)
      self.logger.critical("Stacktrace: " + traceback.format_exc())
        
  def setupRefreshChat(self):
    try:
      result = self.api.getMessages(self.cfg["bounds"], -1, -1, 1, False)["result"]
      self.lastChatTimestamp = result[0][1]
      Thread(target=self.chatLookback, args=(long(self.lastChatTimestamp)-(long(self.cfg["chatLookbackHours"])*3600000), self.lastChatTimestamp)).start()
    except Exception as e:
      self.logger.critical("Exception: " + str(type(e)) + ": " + e.message)
      self.logger.critical("Stacktrace: " + traceback.format_exc())

  def refreshChat(self):
    try:
      response = self.api.getMessages(self.cfg["bounds"], self.lastChatTimestamp, -1, 100, False)
      if "result" in response:
        result = response["result"]
        if(len(result) == 0): return
        self.lastChatTimestamp = result[0][1]
        for message in result:
          plext = message[2]["plext"]
          if plext["plextType"] == "SYSTEM_BROADCAST" or plext["plextType"] == "SYSTEM_NARROWCAST":
            self.trackPlayers(plext, long(message[1]))
    except Exception as e:
      self.logger.critical("Exception: " + str(type(e)) + ": " + e.message)
      self.logger.critical("Stacktrace: " + traceback.format_exc())
      
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
        entry = {"when" : long(-1), "where" : "", "player" : player}
        self.playerHistory[key] = entry
      if(entry["when"] < timestamp):
        entry["when"] = timestamp
        entry["where"] = portal
        
  @botcmd
  def helo(self, mess, args):
    return "Hello World"
  
  @botcmd
  def inv(self, mess, args):
    if self.cfg["master"] != mess.getFrom().getStripped():
      return None
    try:
      self.inventoryLock.acquire()
      if len(args) == 0:
        return "Your inventory holds " + str(len(self.inventory)) + "/2000 items.\n"
      elif args.strip() == "full":
        lines = self.invToStrings()
        out = ""
        for line in lines:
          out += line + "\n";
        return out
    finally:
      self.inventoryLock.release()
  
  @botcmd
  def stat(self, message, args):
    if self.cfg["master"] != mess.getFrom().getStripped():
      return None
    try:
      self.inventoryLock.acquire()
      if len(args) == 0:
        lines = self.statsToStrings()
        str = ""
        first = True
        for line in lines:
          if not first:
            str += "\n"
          else:
            first = False
          str += line
        return str
      elif args.strip() == "rst" or args.strip() == "reset":
        self.inventory.resetStats()
        return "Stats resetted"
    finally:
      self.inventoryLock.release()
      
  @botcmd
  def seen(self, message, args):
    if len(args.strip()) == 0:
      return "Please specify a nickname"
    
    output = ""
    tokens = args.strip().split(" ")
    print len(tokens)
    for key in tokens:
      if key in self.playerHistory:
        entry = self.playerHistory[key]
        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(entry["when"] / 1000.0)
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        deltaStr = ""
        if(delta.days > 0):
          deltaStr += str(delta.days) + "d "
        if(hours > 0):
          deltaStr += str(hours) + "h "
        deltaStr += str(minutes) + "m"
        output += entry["player"] + " was last seen " + deltaStr + " ago on " + entry["where"] + "\n"
      else:
        output += "Can't remember " + key + "\n"
    return output
  
  def invToStrings(self):
    lines = []
    line = "Bursters:\t\t"
    for num in self.inventory.numBursters.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Resonators:\t\t"
    for num in self.inventory.numResos.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Powercubes:\t\t"
    for num in self.inventory.numCubes.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Shield:\t\t"
    for num in self.inventory.numShields.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "Flipcards:\t\t"
    for num in self.inventory.numFlipCards.itervalues():
      line += str(num) + " "
    
    line = "ForceAmps:\t\t"
    for num in self.inventory.numForceAmps.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Heatsinks:\t\t"
    for num in self.inventory.numHeatSinks.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "LinkAmps:\t\t"
    for num in self.inventory.numLinkAmplifiers.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "Multihacks:\t\t"
    for num in self.inventory.numMultihacks.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "Turrets:\t\t"
    for num in self.inventory.numTurrets.itervalues():
      line += str(num) + " "
    lines.append(line)
    lines.append("Medias: " + str(sum(self.inventory.numMedias.values())))
    lines.append("Keys: " + str(self.inventory.numKeys))
    lines.append("Total: " + str(len(self.inventory)))
    return lines

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
    shields = self.inventory.stats["shields"][PortalMod.COMMON]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "C (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    shields = self.inventory.stats["shields"][PortalMod.RARE]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "R (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    shields = self.inventory.stats["shields"][PortalMod.VERY_RARE]
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

def main(argv=None):
  if argv is None:
    argv = sys.argv
    
  daemonize = True
  if("no-daemon" in argv):
    daemonize = False
    argv.remove("no-daemon")

  logger = logging.getLogger("ingressbot")
  if daemonize:
    syslogHandler = logging.handlers.SysLogHandler(address="/dev/log", facility=logging.handlers.SysLogHandler.LOG_DAEMON)
    syslogHandler.setFormatter(logging.Formatter('%(asctime)s %(name)s: %(levelname)s %(message)s', '%b %e %H:%M:%S'))
    logger.addHandler(syslogHandler)
  else:
    logger.addHandler(logging.StreamHandler())
  
  try:
    with open(os.path.expanduser("~/.ingressbot.pwd"), "rb") as f:
      pwd = json.load(f)
    with open(os.path.expanduser("~/.ingressbot.cfg"), "rb") as f:
      cfg = json.load(f)
    
    bot = Ingressbot(pwd, cfg)
    if daemonize:
      daemon = daemon.runner.DaemonRunner(bot)
      daemon.daemon_context.signal_map[signal.SIGTERM] = lambda signal, frame : bot.stop()
      daemon.do_action()
    else:
      bot.run()

  except Exception as e:
    logger.critical("Exception: " + str(type(e)) + ": " + e.message)
    logger.critical("Stacktrace: " + traceback.format_exc())

if __name__ == "__main__":
    sys.exit(main())
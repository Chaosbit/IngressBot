import datetime

class GameEntity(object):
  pass

class PortalKey(GameEntity):
  pass

class LevelEntity(GameEntity):
  def __init__(self, level):
    self.level = level
        
class PortalMod(GameEntity):
  pass

class Burster(LevelEntity):
  def __init__(self, level):
    super(Burster, self).__init__(level)
        
class Resonator(LevelEntity):
  def __init__(self, level):
    super(Resonator, self).__init__(level)
        
class PowerCube(LevelEntity):
  def __init__(self, level):
    super(PowerCube, self).__init__(level)
        
class Shield(PortalMod):
  COMMON, RARE, VERY_RARE = range(3)
  def __init__(self, rarity):
    self.rarity = rarity
        
class FlipCard(GameEntity):
  ADA, JARVIS = range(2)

  def __init__(self, cardType):
    self.cardType = cardType
        
class Inventory(dict):
  def __init__(self):
    self.lastQueryTimestamp = -1
    self.numKeys = 0
    self.numBursters = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
    self.numResos = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
    self.numCubes = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
    self.numFlipCards = {FlipCard.ADA : 0, FlipCard.JARVIS : 0}
    self.numShields = {Shield.COMMON : 0, Shield.RARE : 0, Shield.VERY_RARE : 0}
    self.resetStats()
    
  def processGameBasket(self, result):
    if(not "gameBasket" in result):
      return
    if(not "result" in result):
      return
    timestamp = long(result["result"])
    gameBasket = result["gameBasket"]
    if("deletedEntityGuids" in gameBasket):
      for guid in gameBasket["deletedEntityGuids"]:
        try:
          item = self[guid]
          if(isinstance(item, Burster)):
            self.numBursters[item.level] -= 1
            self.stats["bursters"][item.level]["-"] += 1
          elif(isinstance(item, Resonator)):
            self.numResos[item.level] -= 1
            self.stats["resos"][item.level]["-"] += 1
          elif(isinstance(item, PowerCube)):
            self.numCubes[item.level] -= 1
            self.stats["cubes"][item.level]["-"] += 1
          elif(isinstance(item, PortalKey)):
            self.numKeys -= 1
          elif(isinstance(item, Shield)):
            self.numShields[item.rarity] -= 1;
            self.stats["shields"][item.rarity]["-"] += 1
          elif(isinstance(item, FlipCard)):
            self.numFlipCards[item.cardType] -= 1;
            self.stats["flipcards"][item.cardType]["-"] += 1
          del(self[guid])
        except KeyError:
          pass
    if("inventory" in gameBasket):
      for item in gameBasket["inventory"]:
        guid = item[0]
        if(guid in self):
          continue
        resourceType = ""
        try:
          resourceType = item[2]["resourceWithLevels"]["resourceType"]
        except:
          pass
        try:
          resourceType = item[2]["resource"]["resourceType"]
        except:
          pass
        try:
          resourceType = item[2]["modResource"]["resourceType"]
        except:
          pass

        if(resourceType == "EMP_BURSTER"):
          level = int(item[2]["resourceWithLevels"]["level"])
          self[guid] = Burster(level)
          self.numBursters[level] += 1
          self.stats["bursters"][level]["+"] += 1
        elif(resourceType == "EMITTER_A"):
          level = int(item[2]["resourceWithLevels"]["level"])
          self[guid] = Resonator(level)
          self.numResos[level] += 1
          self.stats["resos"][level]["+"] += 1
        elif(resourceType == "POWER_CUBE"):
          level = int(item[2]["resourceWithLevels"]["level"])
          self[guid] = PowerCube(level)
          self.numCubes[level] += 1 
          self.stats["cubes"][level]["+"] += 1
        elif(resourceType == "RES_SHIELD"):
          rarity = item[2]["modResource"]["rarity"]
          if(rarity == "COMMON"):
            self[guid] = Shield(Shield.COMMON)
            self.numShields[Shield.COMMON] += 1;
          elif(rarity == "RARE"):
            self[guid] = Shield(Shield.RARE)
            self.numShields[Shield.RARE] += 1;
          elif(rarity == "VERY_RARE"):
            self[guid] = Shield(Shield.VERY_RARE)
            self.numShields[Shield.VERY_RARE] += 1;
          self.stats["shields"][self[guid].rarity]["+"] += 1
        elif(resourceType == "PORTAL_LINK_KEY"):
          self[guid] = PortalKey()
          self.numKeys += 1
        elif(resourceType == "FLIP_CARD"):
          t = item[2]["flipCard"]["flipCardType"]
          if(t == "ADA"):
            self[guid] = FlipCard(FlipCard.ADA)
            self.numFlipCards[FlipCard.ADA] += 1;
          elif(t == "JARVIS"):
            self[guid] = FlipCard(FlipCard.JARVIS)
            self.numFlipCards[FlipCard.JARVIS] += 1;
          self.stats["shields"][self[guid].cardType]["+"] += 1
    if(self.lastQueryTimestamp <= 0):
      self.resetStats()
    self.lastQueryTimestamp = timestamp

  def toStrings(self):
    lines = []
    line = "B: "
    for num in self.numBursters.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "R: "
    for num in self.numResos.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "C: "
    for num in self.numCubes.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "S: "
    for num in self.numShields.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "F: "
    for num in self.numFlipCards.itervalues():
      line += str(num) + " "
    lines.append(line)
    lines.append("K: " + str(self.numKeys))
    lines.append("Total: " + str(len(self)))
    return lines
  
  def resetStats(self):
    self.stats = {
      "startTime" : datetime.datetime.now(),
      "bursters" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "resos" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "cubes" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "flipcards" : {FlipCard.ADA : {"+" : 0, "-" : 0}, FlipCard.JARVIS : {"+" : 0, "-" : 0}},
      "shields" : {Shield.COMMON : {"+" : 0, "-" : 0}, Shield.RARE : {"+" : 0, "-" : 0}, Shield.VERY_RARE : {"+" : 0, "-" : 0}}
    }
  
  def statsToStrings(self):
    lines =  []
    delta = datetime.datetime.now() - self.stats["startTime"]
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    deltaStr = ""
    if(delta.days > 0):
      deltaStr += str(delta.days) + "d "
    if(hours > 0):
      deltaStr += str(hours) + "h "
    deltaStr += str(minutes) + "m"
    lines.append("Stats since " + self.stats["startTime"].strftime("%a, %d. %b %Y %H:%M") + " (" + deltaStr + " ago)")
    
    line = ""
    for l in range(1, 8):
      bursters = self.stats["bursters"][l]
      if(bursters["+"] != 0 or bursters["-"] != 0):
        line += "L" + str(l) + "(+" + str(bursters["+"]) + ",-" + str(bursters["-"]) + ") "
    if(len(line) > 0):
      lines.append("B: " + line)

    line = ""
    for l in range(1, 8):
      resos = self.stats["resos"][l]
      if(resos["+"] != 0 or resos["-"] != 0):
        line += "L" + str(l) + "(+" + str(resos["+"]) + ",-" + str(resos["-"]) + ") "
    if(len(line) > 0):
      lines.append("R: " + line)
      
    line = ""
    for l in range(1, 8):
      cubes = self.stats["cubes"][l]
      if(cubes["+"] != 0 or cubes["-"] != 0):
        line += "L" + str(l) + "(+" + str(cubes["+"]) + ",-" + str(cubes["-"]) + ") "
    if(len(line) > 0):
      lines.append("C: " + line)
      
    line = ""
    shields = self.stats["shields"][Shield.COMMON]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "C (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    shields = self.stats["shields"][Shield.RARE]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "R (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    shields = self.stats["shields"][Shield.VERY_RARE]
    if(shields["+"] != 0 or shields["-"] != 0):
      line += "VR (+" + str(shields["+"]) + ",-" + str(shields["-"]) + ") "
    if(len(line) > 0):
      lines.append("S: " + line)
      
    line = ""
    flipcards = self.stats["flipcards"][FlipCard.ADA]
    if(flipcards["+"] != 0 or flipcards["-"] != 0):
      line += "A (+" + str(flipcards["+"]) + ",-" + str(flipcards["-"]) + ") "
    flipcards = self.stats["flipcards"][FlipCard.JARVIS]
    if(flipcards["+"] != 0 or flipcards["-"] != 0):
      line += "J (+" + str(flipcards["+"]) + ",-" + str(flipcards["-"]) + ") "
    if(len(line) > 0):
      lines.append("F: " + line)
      
    if(len(lines) == 1):
      lines.append("Nothing happened")
    return lines
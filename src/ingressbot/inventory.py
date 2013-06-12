import datetime

class GameEntity(object):
  pass

class PortalKey(GameEntity):
  pass

class LevelEntity(GameEntity):
  def __init__(self, level):
    self.level = level
        
class PortalMod(GameEntity):
  COMMON, RARE, VERY_RARE = range(3)
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
  def __init__(self, rarity):
    self.rarity = rarity
    
class ForceAmp(PortalMod):
  def __init__(self, rarity):
    self.rarity = rarity
    
class HeatSink(PortalMod):
  def __init__(self, rarity):
    self.rarity = rarity
    
class LinkAmplifier(PortalMod):
  def __init__(self, rarity):
    self.rarity = rarity
    
class Multihack(PortalMod):
  def __init__(self, rarity):
    self.rarity = rarity
    
class Turret(PortalMod):
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
    self.numShields = {PortalMod.COMMON : 0, PortalMod.RARE : 0, PortalMod.VERY_RARE : 0}
    self.numForceAmps = {PortalMod.COMMON : 0, PortalMod.RARE : 0, PortalMod.VERY_RARE : 0}
    self.numHeatSinks = {PortalMod.COMMON : 0, PortalMod.RARE : 0, PortalMod.VERY_RARE : 0}
    self.numLinkAmplifiers = {PortalMod.COMMON : 0, PortalMod.RARE : 0, PortalMod.VERY_RARE : 0}
    self.numMultihacks = {PortalMod.COMMON : 0, PortalMod.RARE : 0, PortalMod.VERY_RARE : 0}
    self.numTurrets = {PortalMod.COMMON : 0, PortalMod.RARE : 0, PortalMod.VERY_RARE : 0}
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
          if(item[2]["modResource"]["rarity"] == "COMMON"):
            rarity = PortalMod.COMMON
          elif(item[2]["modResource"]["rarity"] == "RARE"):
            rarity = PortalMod.RARE
          elif(item[2]["modResource"]["rarity"] == "VERY_RARE"):
            rarity = PortalMod.VERY_RARE
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
        elif(resourceType == "RES_SHIELD"):
          self[guid] = Shield(rarity)
          self.numShields[rarity] += 1;
          self.stats["shields"][rarity]["+"] += 1
        elif(resourceType == "HEATSINK"):
          self[guid] = HeatSink(rarity)
          self.numHeatSinks[rarity] += 1;
          self.stats["heatsinks"][rarity]["+"] += 1
        elif(resourceType == "TURRET"):
          self[guid] = Turret(rarity)
          self.numTurrets[rarity] += 1;
          self.stats["turrets"][rarity]["+"] += 1
        elif(resourceType == "LINK_AMPLIFIER"):
          self[guid] = LinkAmplifier(rarity)
          self.numLinkAmplifiers[rarity] += 1;
          self.stats["linkamplifiers"][rarity]["+"] += 1
        elif(resourceType == "FORCE_AMP"):
          self[guid] = ForceAmp(rarity)
          self.numForceAmps[rarity] += 1;
          self.stats["forceamps"][rarity]["+"] += 1
        elif(resourceType == "MULTIHACK"):
          self[guid] = Multihack(rarity)
          self.numMultihacks[rarity] += 1;
          self.stats["multihacks"][rarity]["+"] += 1
        else:
          print item
    if(self.lastQueryTimestamp <= 0):
      self.resetStats()
    self.lastQueryTimestamp = timestamp

  def toStrings(self):
    lines = []
    line = "Bursters:\t\t"
    for num in self.numBursters.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Resonators:\t\t"
    for num in self.numResos.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Powercubes:\t\t"
    for num in self.numCubes.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Shield:\t\t"
    for num in self.numShields.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "Flipcards:\t\t"
    for num in self.numFlipCards.itervalues():
      line += str(num) + " "
    
    line = "ForceAmps:\t\t"
    for num in self.numForceAmps.itervalues():
      line += str(num) + " "
    lines.append(line)

    line = "Heatsinks:\t\t"
    for num in self.numHeatSinks.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "LinkAmps:\t\t"
    for num in self.numLinkAmplifiers.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "Multihacks:\t\t"
    for num in self.numMultihacks.itervalues():
      line += str(num) + " "
    lines.append(line)
    
    line = "Turrets:\t\t"
    for num in self.numTurrets.itervalues():
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
      "shields" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "forceamps" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "heatsinks" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "linkamplifiers" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "multihacks" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "turrets" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}}
    }

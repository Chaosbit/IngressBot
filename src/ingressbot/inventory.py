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
    
class Media(LevelEntity):
  def __init__(self, level):
    super(Media, self).__init__(level)
        
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
    self.bursters = {1:dict(),2:dict(),3:dict(),4:dict(),5:dict(),6:dict(),7:dict(),8:dict()}
    self.resonators = {1:dict(),2:dict(),3:dict(),4:dict(),5:dict(),6:dict(),7:dict(),8:dict()}
    self.cubes = {1:dict(),2:dict(),3:dict(),4:dict(),5:dict(),6:dict(),7:dict(),8:dict()}
    self.medias = {1:dict(),2:dict(),3:dict(),4:dict(),5:dict(),6:dict(),7:dict(),8:dict()}
    self.flipCards = {FlipCard.ADA:dict(),FlipCard.JARVIS:dict()}
    self.shields = {PortalMod.COMMON:dict(),PortalMod.RARE:dict(),PortalMod.VERY_RARE:dict()}
    self.forceAmps = {PortalMod.COMMON:dict(),PortalMod.RARE:dict(),PortalMod.VERY_RARE:dict()}
    self.heatSinks = {PortalMod.COMMON:dict(),PortalMod.RARE:dict(),PortalMod.VERY_RARE:dict()}
    self.linkAmplifiers = {PortalMod.COMMON:dict(),PortalMod.RARE:dict(),PortalMod.VERY_RARE:dict()}
    self.multihacks = {PortalMod.COMMON:dict(),PortalMod.RARE:dict(),PortalMod.VERY_RARE:dict()}
    self.turrets = {PortalMod.COMMON:dict(),PortalMod.RARE:dict(),PortalMod.VERY_RARE:dict()}
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
          del(self[guid])
          if(isinstance(item, Burster)):
            del(self.bursters[item.level][guid])
            self.stats["bursters"][item.level]["-"] += 1
          elif(isinstance(item, Resonator)):
            del(self.resonators[item.level][guid])
            self.stats["resos"][item.level]["-"] += 1
          elif(isinstance(item, PowerCube)):
            del(self.cubes[item.level][guid])
            self.stats["cubes"][item.level]["-"] += 1
          elif(isinstance(item, Media)):
            del(self.medias[item.level][guid])
            self.stats["medias"][item.level]["-"] += 1
          elif(isinstance(item, PortalKey)):
            self.numKeys -= 1
          elif(isinstance(item, Shield)):
            del(self.shields[item.rarity][guid])
            self.stats["shields"][item.rarity]["-"] += 1
          elif(isinstance(item, ForceAmp)):
            del(self.forceAmps[item.rarity][guid])
            self.stats["forceamps"][item.rarity]["-"] += 1
          elif(isinstance(item, HeatSink)):
            del(self.heatSinks[item.rarity][guid])
            self.stats["heatsinks"][item.rarity]["-"] += 1
          elif(isinstance(item, LinkAmplifier)):
            del(self.linkAmplifiers[item.rarity][guid])
            self.stats["linkamplifiers"][item.rarity]["-"] += 1
          elif(isinstance(item, Multihack)):
            del(self.multiHacks[item.rarity][guid])
            self.stats["multihacks"][item.rarity]["-"] += 1
          elif(isinstance(item, Turret)):
            del(self.turrets[item.rarity][guid])
            self.stats["turrets"][item.rarity]["-"] += 1
          elif(isinstance(item, FlipCard)):
            del(self.flipCards[item.cardType][guid])
            self.stats["flipcards"][item.cardType]["-"] += 1
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
          item = Burster(level)
          self[guid] = item
          self.bursters[level][guid] = item
          self.stats["bursters"][level]["+"] += 1
        elif(resourceType == "EMITTER_A"):
          level = int(item[2]["resourceWithLevels"]["level"])
          item = Resonator(level)
          self[guid] = item
          self.resonators[level][guid] = item
          self.stats["resos"][level]["+"] += 1
        elif(resourceType == "POWER_CUBE"):
          level = int(item[2]["resourceWithLevels"]["level"])
          item = PowerCube(level)
          self[guid] = item
          self.cubes[level][guid] = item
          self.stats["cubes"][level]["+"] += 1
        elif(resourceType == "MEDIA"):
          level = int(item[2]["resourceWithLevels"]["level"])
          item = Media(level)
          self[guid] = item
          self.medias[level][guid] = item
          self.stats["medias"][level]["+"] += 1
        elif(resourceType == "PORTAL_LINK_KEY"):
          self[guid] = PortalKey()
          self.numKeys += 1
        elif(resourceType == "FLIP_CARD"):
          t = item[2]["flipCard"]["flipCardType"]
          if(t == "ADA"):
            item = FlipCard(FlipCard.ADA)
            self[guid] = item
            self.flipCards[FlipCard.ADA][guid] = item
          elif(t == "JARVIS"):
            item = FlipCard(FlipCard.JARVIS)
            self[guid] = item
            self.flipCards[FlipCard.JARVIS][guid] = item
          self.stats["shields"][self[guid].cardType]["+"] += 1
        elif(resourceType == "RES_SHIELD"):
          item = Shield(rarity)
          self[guid] = item
          self.shields[rarity][guid] = item
          self.stats["shields"][rarity]["+"] += 1
        elif(resourceType == "HEATSINK"):
          item = HeatSink(rarity)
          self[guid] = item
          self.heatSinks[rarity][guid] = item
          self.stats["heatsinks"][rarity]["+"] += 1
        elif(resourceType == "TURRET"):
          item = Turret(rarity)
          self[guid] = item
          self.turrets[rarity][guid] = item
          self.stats["turrets"][rarity]["+"] += 1
        elif(resourceType == "LINK_AMPLIFIER"):
          item = LinkAmplifier(rarity)
          self[guid] = item
          self.linkAmplifiers[rarity][guid] = item
          self.stats["linkamplifiers"][rarity]["+"] += 1
        elif(resourceType == "FORCE_AMP"):
          item = ForceAmp(rarity)
          self[guid] = item
          self.forceAmps[rarity][guid] = item
          self.stats["forceamps"][rarity]["+"] += 1
        elif(resourceType == "MULTIHACK"):
          item = Multihack(rarity)
          self[guid] = item
          self.multihacks[rarity][guid] = item
          self.stats["multihacks"][rarity]["+"] += 1
        else:
          print item
    if(self.lastQueryTimestamp <= 0):
      self.resetStats()
    self.lastQueryTimestamp = timestamp

  def resetStats(self):
    self.stats = {
      "startTime" : datetime.datetime.now(),
      "bursters" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "resos" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "cubes" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "medias" : {1: {"+" : 0, "-" : 0}, 2: {"+" : 0, "-" : 0}, 3: {"+" : 0, "-" : 0}, 4: {"+" : 0, "-" : 0}, 5: {"+" : 0, "-" : 0}, 6: {"+" : 0, "-" : 0}, 7: {"+" : 0, "-" : 0}, 8: {"+" : 0, "-" : 0}},
      "flipcards" : {FlipCard.ADA : {"+" : 0, "-" : 0}, FlipCard.JARVIS : {"+" : 0, "-" : 0}},
      "shields" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "forceamps" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "heatsinks" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "linkamplifiers" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "multihacks" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}},
      "turrets" : {PortalMod.COMMON : {"+" : 0, "-" : 0}, PortalMod.RARE : {"+" : 0, "-" : 0}, PortalMod.VERY_RARE : {"+" : 0, "-" : 0}}
    }

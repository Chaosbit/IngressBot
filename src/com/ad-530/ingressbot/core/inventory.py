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
    self.lastQueryTimestamp = 0
    self.numKeys = 0
    self.numBursters = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
    self.numResos = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
    self.numCubes = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
    self.numFlipCards = {FlipCard.ADA : 0, FlipCard.JARVIS : 0}
    self.numShields = {Shield.COMMON : 0, Shield.RARE : 0, Shield.VERY_RARE : 0}
    
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
          elif(isinstance(item, Resonator)):
            self.numResos[item.level] -= 1
          elif(isinstance(item, PowerCube)):
            self.numCubes[item.level] -= 1
          elif(isinstance(item, PortalKey)):
            self.numKeys -= 1
          elif(isinstance(item, Shield)):
            if(item.rarity == Shield.COMMON):
              self.numShields[Shield.COMMON] -= 1;
            elif(item.rarity == Shield.RARE):
              self.numShields[Shield.RARE] -= 1;
            elif(item.rarity == Shield.VERY_RARE):
              self.numShields[Shield.VERY_RARE] -= 1;
          elif(isinstance(item, FlipCard)):
            if(item.cardType == FlipCard.ADA):
              self.numFlipCards[FlipCard.ADA] -= 1;
            elif(item.cardType == FlipCard.JARVIS):
              self.numFlipCards[FlipCard.JARVIS] -= 1;
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
        elif(resourceType == "EMITTER_A"):
          level = int(item[2]["resourceWithLevels"]["level"])
          self[guid] = Resonator(level)
          self.numResos[level] += 1 
        elif(resourceType == "POWER_CUBE"):
          level = int(item[2]["resourceWithLevels"]["level"])
          self[guid] = PowerCube(level)
          self.numCubes[level] += 1 
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
    self.lastQueryTimestamp = timestamp


  def doPrint(self):
    line = "B:\t"
    for num in self.numBursters.itervalues():
      line += str(num) + "\t"
    print line

    line = "R:\t"
    for num in self.numResos.itervalues():
      line += str(num) + "\t"
    print line

    line = "C:\t"
    for num in self.numCubes.itervalues():
      line += str(num) + "\t"
    print line

    line = "S:\t"
    for num in self.numShields.itervalues():
      line += str(num) + "\t"
    print line

    line = "F:\t"
    for num in self.numFlipCards.itervalues():
      line += str(num) + "\t"
    print line

    print "K:\t" + str(self.numKeys)
    print "Total:\t" + str(len(self))
    print ""
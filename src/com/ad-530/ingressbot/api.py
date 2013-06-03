import copy
import json
import requests
import S2

from pprint import pprint

HANDSHAKE_PARAMS = {
  "nemesisSoftwareVersion" : "2013-05-23T16:34:52Z fac47da11030 opt", 
  "deviceSoftwareVersion" : "4.1.1"
}
URLS = {
  "CLIENT_LOGIN" : "https://www.google.com/accounts/ClientLogin",
  "GAME_API" : "https://betaspike.appspot.com"
}
PATHS = {
  "LOGIN" : "/_ah/login",
  "HANDSHAKE" : "/handshake",
  "DROP_ITEM" : "/rpc/gameplay/dropItem",
  "SAY" : "/rpc/player/say",
  "INVENTORY" : "/rpc/playerUndecorated/getInventory",
  "PLEXTS" : "/rpc/playerUndecorated/getPaginatedPlexts"
}
HEADERS = {
  "HANDSHAKE" : {      
    "Accept-Charset" : "utf-8",
    "Cache-Control" : "max-age=0"
  },
  "REQUEST" : {
    "Content-Type" : "application/json;charset=UTF-8", 
    "User-Agent" : "Nemesis (gzip)"
  }
}

class Api(object):
  def __init__(self, email, password):
    self.cachedGetMessagesBounds = set()
    authParams = {"Email":   email, "Passwd":  password, "service": "ah", "source":  "IngressBot", "accountType": "HOSTED_OR_GOOGLE"}
    request =  requests.post(URLS["CLIENT_LOGIN"], params=authParams)
    status = int(request.status_code)
    response = dict(x.split("=") for x in request.content.split("\n") if x)
    if(status == 200):
      try:
        authToken = response["Auth"]
      except:
        raise RuntimeError("Authentication failed: Bad Response")
    elif(status == 403):
      error = response["Error"]
      if(error == "BadAuthentication"):
        raise RuntimeError("Authentication failed: Username or password wrong")
      elif(error == "NotVerified"):
        raise RuntimeError("Authentication failed: Account email address has not been verified")
      elif(error == "TermsNotAgreed"):
        raise RuntimeError("Authentication failed: User has not agreed to Googles terms of service")
      elif(error == "CaptchaRequired"):
        raise RuntimeError("Authentication failed: CAPTCHA required")
      elif(error == "AccountDeleted"):
        raise RuntimeError("Authentication failed: User account has been deleted")
      elif(error == "AccountDisabled"):
        raise RuntimeError("Authentication failed: User account has been disabled")
      elif(error == "ServiceDisabled"):
        raise RuntimeError("Authentication failed: Service disabled")
      elif(error == "ServiceUnavailable"):
        raise RuntimeError("Authentication failed: Service unavailable")
      else:
        raise RuntimeError("Authentication failed: Unknown reason")
    else:
      raise RuntimeError("Authentication failed: Bad Response")
    
    request = requests.post(URLS["GAME_API"] + PATHS["LOGIN"], params={"auth" : authToken})
    self.cookies = request.cookies
    self.headers = copy.deepcopy(HEADERS)

    urlParams = {"json" : json.dumps(HANDSHAKE_PARAMS)}
    request = requests.get(URLS["GAME_API"] + PATHS["HANDSHAKE"], verify=False, params=urlParams, headers=self.headers["HANDSHAKE"], cookies=self.cookies)
    try:
      handshakeResult = json.loads(request.content.replace("while(1);", ""))["result"]
    except:
      raise RuntimeError("Authentication with Ingress severs failed for unknown reason")
    if(handshakeResult["versionMatch"] != "CURRENT"):
      raise RuntimeError("Software version not up-to-date")
    if("xsrfToken" not in handshakeResult):
      raise RuntimeError("Authentication with Ingress severs failed for unknown reason")
    self.headers["REQUEST"]["X-XsrfToken"] = handshakeResult["xsrfToken"]
    self.nickname = handshakeResult["nickname"]
    self.playerGUID = handshakeResult["playerEntity"][0]
      
  def getInventory(self, lastQueryTimestamp):
    request = requests.post(URLS["GAME_API"] + PATHS["INVENTORY"], headers = self.headers["REQUEST"], data = json.dumps({"params" : {"lastQueryTimestamp": lastQueryTimestamp}}), cookies=self.cookies)
    try:
      return json.loads(request.content.replace("while(1);", ""))
    except:
      print request.content
      raise
    
  def getMessages(self, bounds, lastTimestamp, maxItems, factionOnly):
    if(self.cachedGetMessagesBounds != set(bounds)):
      self.cachedGetMessagescellsAsHex = []
      rect = S2.S2LatLngRect(S2.S2LatLng.FromDegrees(bounds["minLat"], bounds["minLng"]), S2.S2LatLng.FromDegrees(bounds["maxLat"], bounds["maxLng"]))
      coverer = S2.S2RegionCoverer()
      coverer.set_min_level(8)
      coverer.set_max_level(12)
      cells = coverer.GetCovering(rect)
      for cell in cells:
        self.cachedGetMessagescellsAsHex.append("%X" % cell.id())
      self.cachedGetMessagesBounds = set(bounds)
    
    request = requests.post(URLS["GAME_API"] + PATHS["PLEXTS"], verify=False, headers = self.headers["REQUEST"], cookies=self.cookies, data = json.dumps(
    {"params" : {
      "desiredNumItems" : str(maxItems),
      "factionOnly": factionOnly,
      "maxTimestampMs": -1,
      "minTimestampMs": lastTimestamp,
      "cellsAsHex" : self.cachedGetMessagescellsAsHex
      }
    }))
    try:
      return json.loads(request.content)
    except:
      print request.content
      raise
    
  def say(self, msg, factionOnly=True):
    requests.post(URLS["GAME_API"] + PATHS["SAY"], headers = self.headers["REQUEST"], data = json.dumps({"params" : {"factionOnly": "true", "message" : msg}}), cookies=self.cookies)
    print "said: " + msg

  def dropItem(self, guid):
    request = requests.post(URLS["GAME_API"] + PATHS["DROP_ITEM"], headers = self.headers["REQUEST"], data = json.dumps(
{"params" : 
  {"itemGuid": guid, "knobSyncTimestamp" : "1370219980525", "playerLocation" : "031192E4,00B63F54", "location" : "031192E4,00B63F54"}}), cookies=self.cookies)
    print request.content
    #pprint(json.loads(request.content))

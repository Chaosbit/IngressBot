import copy
import json
import lxml.html
import requests
from StringIO import StringIO

HANDSHAKE_PARAMS = {
  "nemesisSoftwareVersion" : "2013-05-23T16:34:52Z fac47da11030 opt", 
  "deviceSoftwareVersion" : "4.1.1"
}
URLS = {
  "CLIENT_LOGIN" : "https://www.google.com/accounts/ClientLogin",
  "SERVICE_LOGIN" : "https://accounts.google.com/ServiceLoginAuth",
  "APPENGINE" : "https://appengine.google.com",
  "GAME_API" : "https://betaspike.appspot.com",
  "INGRESS" : "http://www.ingress.com"
}
PATHS = {
  "LOGIN" : "/_ah/login",
  "CONFLOGIN" : "/_ah/conflogin",
  "API" : {
    "HANDSHAKE" : "/handshake",
    "DROP_ITEM" : "/rpc/gameplay/dropItem",
    "SAY" : "/rpc/player/say",
    "INVENTORY" : "/rpc/playerUndecorated/getInventory",
    "PLEXTS" : "/rpc/playerUndecorated/getPaginatedPlexts"
  },
  "INTEL" : {
    "BASE" : "/intel",
    "PLEXTS" : "/rpc/dashboard.getPaginatedPlextsV2"
  }
}
HEADERS = {
  "HANDSHAKE" : {      
    "Accept-Charset" : "utf-8",
    "Cache-Control" : "max-age=0"
  },
  "API" : {
    "Content-Type" : "application/json;charset=UTF-8", 
    "User-Agent" : "Nemesis (gzip)"
  },
  "INTEL" : {
    "Referer" : r"http://www.ingress.com/intel",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"
  }
}

class Api(object):
  def __init__(self, email, password):
    self.headers = copy.deepcopy(HEADERS)
    self.authApi(email, password)
    self.authIntel(email, password)
      
  def authApi(self, email, password):
    authParams = {"Email":   email, "Passwd":  password, "service": "ah", "source":  "IngressBot", "accountType": "HOSTED_OR_GOOGLE"}
    request =  requests.post(URLS["CLIENT_LOGIN"], data=authParams)
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
    
    request = requests.get(URLS["GAME_API"] + PATHS["LOGIN"], params={"auth" : authToken})
    self.cookiesApi = request.cookies

    urlParams = {"json" : json.dumps(HANDSHAKE_PARAMS)}
    request = requests.get(URLS["GAME_API"] + PATHS["API"]["HANDSHAKE"], verify=False, params=urlParams, headers=self.headers["HANDSHAKE"], cookies=self.cookiesApi)
    try:
      handshakeResult = json.loads(request.content.replace("while(1);", ""))["result"]
    except:
      raise RuntimeError("Authentication with Ingress severs failed for unknown reason")
    if(handshakeResult["versionMatch"] != "CURRENT"):
      raise RuntimeError("Software version not up-to-date")
    if("xsrfToken" not in handshakeResult):
      raise RuntimeError("Authentication with Ingress severs failed for unknown reason")
    self.headers["API"]["X-XsrfToken"] = handshakeResult["xsrfToken"]
    self.nickname = handshakeResult["nickname"]
    self.playerGUID = handshakeResult["playerEntity"][0]
    
  def authIntel(self, email, password):
    params = {"service" : "ah" , "passive" : "true", "continue" : URLS["APPENGINE"] + PATHS["CONFLOGIN"] + "?continue=http://www.ingress.com/intel"}
    request = requests.get(URLS["SERVICE_LOGIN"], params=params, verify=False)
    tree = lxml.html.parse(StringIO(request.content))
    root = tree.getroot()
    for form in root.xpath('//form[@id="gaia_loginform"]'):
        for field in form.getchildren():
            if 'name' in field.keys():
              name = field.get('name')
              if name == "dsh":
                params["dsh"] = field.get('value')
              elif name == "GALX":
                params["GALX"] = field.get('value')
    params["Email"] = email
    params["Passwd"] = password
    
    request = requests.post(URLS["SERVICE_LOGIN"], cookies=request.cookies, data=params, verify=False)
    tree = lxml.html.parse(StringIO(request.content))
    root = tree.getroot()
    for field in root.xpath('//input'):
      if 'name' in field.keys():
        if field.get('name') == "state":
          params["state"] = field.get('value')
    params["submit_true"] = "Allow"
    
    request = requests.post(URLS["APPENGINE"] + PATHS["CONFLOGIN"], cookies=request.cookies, data=params, verify=False)
    hasSID = False
    hasCSRF = False
    for cookie in request.cookies:
      if cookie.name == "ACSID":
        hasSID = True
      if cookie.name == "csrftoken":
        hasCSRF = True
        self.headers["INTEL"]["X-CSRFToken"] = cookie.value
    if not (hasSID and hasCSRF):
      raise RuntimeError("Authentication failed: Unknown reason")
    self.cookiesIntel = request.cookies
  
  def getInventory(self, lastQueryTimestamp):
    request = requests.post(URLS["GAME_API"] + PATHS["API"]["INVENTORY"], headers = self.headers["API"], data = json.dumps({"params" : {"lastQueryTimestamp": lastQueryTimestamp}}), cookies=self.cookiesApi)
    try:
      return json.loads(request.content.replace("while(1);", ""))
    except:
      print request.content
      raise
    
  def getMessages(self, bounds, minTimestamp, maxTimestamp, maxItems, factionOnly):
    payload = {
      "factionOnly" : factionOnly,
      "desiredNumItems" : maxItems,
      "minLatE6": bounds["minLatE6"],
      "minLngE6" : bounds["minLngE6"],
      "maxLatE6" : bounds["maxLatE6"],
      "maxLngE6" : bounds["maxLngE6"],
      "minTimestampMs" : minTimestamp,
      "maxTimestampMs" : maxTimestamp,
      "method" : "dashboard.getPaginatedPlextsV2"
    }
    request = requests.post(URLS["INGRESS"] + PATHS["INTEL"]["PLEXTS"], cookies=self.cookiesIntel, headers=self.headers["INTEL"], data = json.dumps(payload))
    try:
      return json.loads(request.content)
    except:
      print request.content
      raise
    
  def say(self, msg, factionOnly=True):
    requests.post(URLS["GAME_API"] + PATHS["API"]["SAY"], headers = self.headers["API"], data = json.dumps({"params" : {"factionOnly": factionOnly, "message" : msg}}), cookies=self.cookiesApi)
    print "said: " + msg

  def dropItem(self, guid):
    request = requests.post(URLS["GAME_API"] + PATHS["API"]["DROP_ITEM"], headers = self.headers["API"], data = json.dumps(
{"params" : 
  {"itemGuid": guid, "knobSyncTimestamp" : "1370219980525", "playerLocation" : "031192E4,00B63F54", "location" : "031192E4,00B63F54"}}), cookies=self.cookiesApi)
    print request.content
    #pprint(json.loads(request.content))

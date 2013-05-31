import copy
import json
import requests

HANDSHAKE_PARAMS = {
  "nemesisSoftwareVersion" : "2013-05-23T16:34:52Z fac47da11030 opt", 
  "deviceSoftwareVersion" : "4.1.1"
}
URLS = {
  "CLIENT_LOGIN" : "https://www.google.com/accounts/ClientLogin",
  "GAME_API" : "https://m-dot-betaspike.appspot.com"
}
PATHS = {
  "LOGIN" : "/_ah/login",
  "HANDSHAKE" : "/handshake",
  "INVENTORY" : "/rpc/playerUndecorated/getInventory"
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
    for rq in request.cookies:
      if(rq.name == "SACSID"):
        cookie = "SACSID=" + rq.value
        break
    if(not cookie):
      raise RuntimeError("Authentication with Ingress severs failed for unknown reason")
    
    self.headers = copy.deepcopy(HEADERS)
    for header in self.headers.itervalues():
      header["Cookie"] = cookie

    urlParams = {"json" : json.dumps(HANDSHAKE_PARAMS)}
    request = requests.get(URLS["GAME_API"] + PATHS["HANDSHAKE"], params=urlParams, headers=self.headers["HANDSHAKE"])
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
      
  def getInventory(self, lastQueryTimestamp):
    request = requests.post(URLS["GAME_API"] + PATHS["INVENTORY"], headers = self.headers["REQUEST"], data = json.dumps({"params" : {"lastQueryTimestamp": lastQueryTimestamp}})
    )
    try:
      return json.loads(request.content.replace("while(1);", ""))
    except:
      print request.content
      raise
    
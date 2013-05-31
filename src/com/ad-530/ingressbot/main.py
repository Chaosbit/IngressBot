#!/usr/bin/python

from core.api import Api
from core.inventory import Inventory

import json
import os.path
from pickle import Pickler, Unpickler
from time import sleep

try:
  with open(os.path.expanduser("~/.ingressbot.pwd"), "rb") as f:
    pwd = json.load(f)
    userEmail = pwd["userEmail"]
    userPassword = pwd["userPassword"]
except:
###################### Ausfuellen ################################
  userEmail    = ""
  userPassword = ""
#################################################################

api = Api(userEmail, userPassword)

try:
  with open(os.path.expanduser("~/.ingressbot.pkl"), "rb") as f:
    unpickler = Unpickler(f)
    inventory = unpickler.load()
except:
  inventory = Inventory()

while(True):
  result = api.getInventory(inventory.lastQueryTimestamp);
  if("gameBasket" in result):
    inventory.processGameBasket(result)
    inventory.doPrint()
    with open(os.path.expanduser("~/.ingressbot.pkl"), "wb") as f:
      pickler = Pickler(f)
      pickler.dump(inventory)
  sleep(5)

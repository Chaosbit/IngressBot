from datetime import datetime
from threading import Event, Thread

import logging

class TimerThread(Thread):
  
  def __init__(self, interval, group=None, setup=None, target=None, name=None, args=(), kwargs=None):
    super(TimerThread, self).__init__(group, target, name, args, kwargs)
    self.__interval = float(interval)
    self.__event = Event()
    self.__setup = setup
    self.logger = logging.getLogger("ingressbot")
  
  def interrupt(self):
    self.__event.set()
    
  def run(self):
    try:
      if not self.__setup is None:
        self.__setup()
      while not self.__event.isSet():
        t1 = datetime.now()
        self.do()
        t2 = datetime.now()
        self.__event.wait(self.__interval - (t2-t1).total_seconds())
    except Exception as e:
      self.logger.critical("ex: " + str(type(e)) + ": " + e.message)
      
  def do(self):
    if self._Thread__target:
      self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
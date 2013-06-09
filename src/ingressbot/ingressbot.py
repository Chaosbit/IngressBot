#!/usr/bin/python

import core
import daemon.runner
import logging
import logging.handlers
import signal

logger = logging.getLogger("ingressbot")
syslogHandler = logging.handlers.SysLogHandler(address="/dev/log", facility=logging.handlers.SysLogHandler.LOG_DAEMON)
syslogHandler.setFormatter(logging.Formatter('%(asctime)s %(name)s: %(levelname)s %(message)s', '%b %e %H:%M:%S'))
logger.addHandler(syslogHandler)

bot = core.Ingressbot()
daemon = daemon.runner.DaemonRunner(bot)
daemon.daemon_context.signal_map[signal.SIGTERM] = lambda signal, frame : bot.stop()

try:
  daemon.do_action()
except Exception as e:
  logger.critical("ex: " + str(type(e)) + ": " + e.message)

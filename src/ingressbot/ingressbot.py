#!/usr/bin/python
import daemon.runner
import logging
import logging.handlers
import signal
import traceback

import core

logger = logging.getLogger("ingressbot")
syslogHandler = logging.handlers.SysLogHandler(address="/dev/log", facility=logging.handlers.SysLogHandler.LOG_DAEMON)
syslogHandler.setFormatter(logging.Formatter('%(asctime)s %(name)s: %(levelname)s %(message)s', '%b %e %H:%M:%S'))
logger.addHandler(syslogHandler)

try:
  bot = core.Ingressbot()
  daemon = daemon.runner.DaemonRunner(bot)
  daemon.daemon_context.signal_map[signal.SIGTERM] = lambda signal, frame : bot.stop()
  daemon.do_action()
except Exception as e:
  logger.critical("Exception: " + str(type(e)) + ": " + e.message)
  logger.critical("Stacktrace: " + traceback.format_exc())

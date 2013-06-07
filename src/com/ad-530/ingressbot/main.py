#!/usr/bin/python
import core

import daemon
import lockfile
import signal

context = daemon.DaemonContext(
  pidfile = lockfile.FileLock('/var/run/ingressbot.pid'),
)

context.signal_map = {
    signal.SIGTERM: core.cleanup,
    signal.SIGHUP: 'terminate'
}

core.setup()

#with context:
core.main()

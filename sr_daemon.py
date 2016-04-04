#!/usr/bin/python
#
# Simple SR Daemon
#
import time
import srmanager.sr
import logging
import signal

def handler(signum, frame):
    logging.info("got signal: {}".format(signum))

# Setup logging
logging.basicConfig(filename='sr.log',level=logging.INFO)
logging.info("SR Daemon starting")

# get SR class
srm = srmanager.sr.SR()

# Handle signals
signal.signal(signal.SIGUSR1, handler)

# grab the latest topology
old = srm.get_topology()

# start with a clean slate, delete all flows
srm.del_all_flows(old)

# now add sr flows
srm.add_sr_flows(old)

# Now just check the toplogy every 60 secs
running = True
while running:
    time.sleep(60)
    new = srm.get_topology()

    # Update the old flows
    logging.info("Updating Topology")
    srm.update_sr_flows(old, new)

logging.info("SR Daemon finished")


#!/usr/bin/python
#
# Simple SR Daemon
#
import time
import srmanager.sr
import logging

# Setup logging
logging.basicConfig(filename='sr.log',level=logging.INFO)
logging.info("SR Daemon starting")

# get SR class
srm = srmanager.sr.SR()

# grab the latest topology
top = srm.get_topology()

# start with a clean slate, delete all flows
srm.del_all_flows(top)

# now add sr flows
srm.add_sr_flows(top)

# Now wait for topology changes
while True:
    srm.listen_to_topology(graph)

    # Update the old flows
    logging.info("Updating Topology")
    top = srm.update_sr_flows(top)

logging.info("SR Daemon finished")


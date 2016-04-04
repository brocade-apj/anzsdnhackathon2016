import time
import srmanager.sr

srm = srmanager.sr.SR()

old = srm.get_topology()

while True:
    time.sleep(5)
    new = srm.get_topology()
    if srm.graphs_equal(old, new):
        print "topologies equal"
    else:
        print "topologies not equal"
        print new
    old = new


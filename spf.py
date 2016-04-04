import json
import sys
import srmanager.sr
import networkx as nx

# Make sure we've got a src & dst
if len(sys.argv) < 2:
  print "Usage: spf src dst"
  sys.exit()

src = sys.argv[1]
dst = sys.argv[2]

srm = srmanager.sr.SR()
top = srm.get_topology()

# Find shortest path
try:
    print "shortest path is {}".format(nx.shortest_path(top, src, dst))
except nx.exception.NetworkXError as e:
    print "can't find path: {}".format(e)


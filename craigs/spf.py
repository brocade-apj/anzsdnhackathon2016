import json
import httplib2
import networkx as nx
import sys

# Make sure we've got a src & dst
if len(sys.argv) < 2:
  print "Usage: spf src dst"
  sys.exit()

src = sys.argv[1]
dst = sys.argv[2]

# Topology Manager URLs
baseUrl = 'http://127.0.0.1:8181/restconf/operational/'
topology = 'network-topology:network-topology/'
id = 'topology/flow:1/'

h = httplib2.Http(".cache")
h.add_credentials('admin', 'admin')

# Get all the edges/links
resp, content = h.request(baseUrl + topology + id , "GET")
topology = json.loads(content)

#did we get anything
if len(topology) == 0:
  print("no toplogies returned")
  exit

# init networkx
graph = nx.Graph()

# Get all the nodes/switches
nodes = topology['topology'][0]['node']
for node in nodes:
  node = node['node-id']
  if node.find('host') == -1:
    graph.add_node(node)
    print node

# Get all links
links = topology['topology'][0]['link']
for link in links:
  if link['link-id'].find('host') == -1:
    edge = (link['destination']['dest-node'], link['source']['source-node'])
    graph.add_edge(*edge)
    print edge

# Check if we've got a path
if not nx.has_path(graph, src, dst):
  print "no path exists"
  sys.exit()

print "shortest path length: {} ".format(nx.shortest_path_length(graph, src, dst))

# Find shortest path
print "shortest path: "
print nx.shortest_path(graph, src, dst)

print "all shortest path: "
print ([p for p in nx.all_shortest_paths(graph, src, dst)])

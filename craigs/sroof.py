import json
import httplib2
import networkx as nx
import sys

# Topology Manager URLs
baseUrl = 'http://127.0.0.1:8181/restconf/operational/'
nettop = 'network-topology:network-topology/'
id = 'topology/flow:1/'

h = httplib2.Http(".cache")
h.add_credentials('admin', 'admin')

# Get all the edges/links
resp, content = h.request(baseUrl + nettop + id , "GET")
topologies = json.loads(content)

#did we get anything
if len(topologies) == 0:
  print("no toplogies returned")
  sys.exit()

topology = topologies['topology'][0]

# init networkx
graph = nx.Graph()

# list of termination points keyed by node-id
tps = {}
nodes = []

# check for nodes 
if 'node' in topology:

    # Get all the nodes/switches
    tnodes = topology['node']
    for node in tnodes:
      nid = node['node-id']
      # only add switches
      if nid.find('host') == -1:
        graph.add_node(nid)
        tps[nid] = []
        # Add termination points
        for tp in node['termination-point']:
            tpid = tp['tp-id']
            tps[nid].append(tpid)
else:
    print "No nodes found"
    
# check for links 
if 'link' in topology:

    # Get all links
    tlinks = topology['link']
    for link in tlinks:
      if link['link-id'].find('host') == -1:
        edge = (link['source']['source-node'], link['destination']['dest-node'])
        srctp = link['source']['source-tp']
        edge += ({ 'source-tp': srctp },)
        graph.add_edge(*edge)
else:
    print "No links found"
    
# Spin thru each node and set the flows
print "Calculate flows for each node"
for snode in graph:
    print "Rules for " + snode
    for tnode in graph:
        # Don't do us
        if snode == tnode:
            continue
        # Add flow for this target
        try:
            sp = nx.shortest_path(graph, snode, tnode)
            nexthop = sp[1]
            srctp = graph[snode][nexthop]['source-tp']
            print("add flow for node {0}: match {1} output {2}".format(snode, tnode, srctp))
        except nx.NetworkXNoPath:
            print("no path for {} to {}".format(snode, tnode))



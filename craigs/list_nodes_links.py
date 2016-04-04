import json
import httplib2
import sys

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

# Get all the nodes/switches
nodes = topology['topology'][0]['node']
for node in nodes:
  node = node['node-id']
  if node.find('host') == -1:
    print node

# Get all links
links = topology['topology'][0]['link']
for link in links:
  if link['link-id'].find('host') == -1:
    edge = (link['destination']['dest-node'], link['source']['source-node'])
    print edge

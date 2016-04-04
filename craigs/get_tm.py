import json
import httplib2

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

links = topology['topology'][0]['link']
print(json.dumps(links, indent=2))

# Get all the nodes/switches
nodes = topology['topology'][0]['node']
print(json.dumps(nodes, indent=2))


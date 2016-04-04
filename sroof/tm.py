#
# Topology Manager stuff
#

import json
import httplib2
import networkx as nx
import sys
from srmanager.controller import Controller 

# Segment Routing class
sr = sid.SID()

h = httplib2.Http(".cache")
h.add_credentials('admin', 'admin')

class TopologyManager():
    '''Topology Manager Class'''

    def __init__(self):
        '''init the controller'''
        self.ctrl = Controller()

    def get_topology(self, tpid='flow:1'):
        '''grab the given topology
        '''

        resp = self.ctrl.gttp_get_request(
                self.ctrl.get_oper_url() 
                + 'network-topology:network-topology/topology/'.format(tpid))

        # Check response code
        if resp is not None:
            if resp.status_code == 200:
                topologies = json.loads(content)

                #did we get anything
                if len(topologies) == 0:
                    raise("no toplogies found")
                return topologies['topology'][0]

        raise("get topology call failed: {}".format(resp.status_code))


#
# Topology Manager stuff
#

import json
import httplib2
import networkx as nx
import os
import sys
import yaml
from srmanager.controller import Controller 

h = httplib2.Http(".cache")
h.add_credentials('admin', 'admin')

class TopologyManager():
    '''Topology Manager Class'''

    def __init__(self, **kwargs):
        '''init the controller'''

        self.ctrl = Controller(**kwargs)

    def get_topology(self, tpid='flow:1'):
        '''grab the given topology
        '''

        resp = self.ctrl.http_get_request(
                self.ctrl.get_operational_url() 
                + '/network-topology:network-topology/topology/{}'.format(tpid))

        # Check response code
        if resp is not None:
            if resp.status_code == 200:
                topologies = json.loads(resp.content)

                #did we get anything
                if len(topologies) == 0:
                    raise(Exception("no toplogies found"))
                return topologies['topology'][0]

        raise(Exception("get topology call failed: {}".format(resp.status_code)))


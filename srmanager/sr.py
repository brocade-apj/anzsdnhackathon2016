import json
import httplib2
import networkx as nx
import sys
import os
import tm
import logging
import client

# Setup logging
logging.basicConfig(filename='sr.log',level=logging.DEBUG)

class SR():
    '''Segment Routing over OpenFlow class'''
    
    def __init__(self, start=16000):
        '''initialise'''

        logging.info("Initialising Segment Routing over OpenFlow")

        # Set the starting SR Block
        self.srgb_start = start

        # Get controller config
        self.config = self.get_config("ctrl.yml")

        # Grab TM
        self.tm = tm.TopologyManager(config=self.config)

        # Grab SRManager
        self.srm = client.Client(config=self.config)

        # init networkx
        self.graph = nx.Graph()
        
    def get_property(self, dic, name, default):
        ''''get property'''

        if name in dic and dic[name] is not None:
            return dic[name]
        if name in os.environ and os.environ[name] is not None:
            return os.environ[name]

        return default


    def get_config(self, file):
        '''grab controller config'''

        props = {}

        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                props = yaml.load(f)

        config = {}
        config['ip']=self.get_property(props,'BSC_IP','127.0.0.1')
        config['port']=self.get_property(props,'BSC_PORT','8181')
        config['username']=self.get_property(props,'BSC_USER','admin')
        config['password']=self.get_property(props,'BSC_PASSWORD','admin')
        config['protocol']=self.get_property(props,'BSC_PROTOCOL','http')
        config['timeout']=self.get_property(props,'BSC_TIMEOUT', 5)

        return config


    def get_topology(self):
        ''''get a new topology and add to a graph and return'''
        # Allocate new graph
        g = nx.Graph()

        # Grab the toplogy from the controller
        topology = self.tm.get_topology()

        # check we've got nodes and links
        if 'node' in topology:

            # Get all the nodes/switches
            tnodes = topology['node']
            for node in tnodes:
              nid = node['node-id']
              # only add switches
              if nid.find('host') == -1:
                g.add_node(nid)
        else:
            logging.info("No nodes found in topology")
            
        # check for links 
        if 'link' in topology:
            
            # Get all links
            tlinks = topology['link']
            for link in tlinks:
                if link['link-id'].find('host') == -1:
                    edge = (link['source']['source-node'], 
                            link['destination']['dest-node'])
                    srctp = link['source']['source-tp']
                    edge += ({ 'source-tp': srctp },)
                    logging.debug('edge added to graph: {}'.format(edge))
                    g.add_edge(*edge)
            else:
                logging.info("No links found in topology")

        # return the new graph
        return g

    def add_sr_flows(self, graph):
                
        # Spin thru each node and set the flows
        logging.debug("Calculate flows for each node")
        for snode in graph:
            logging.debug("Rules for " + snode)

            # Add low priority goto to SR flow
            self.srm.add_goto_sr_flow(snode)

            for tnode in graph:
                # add rule for every other node (i.e. not us)
                if snode == tnode:
                    continue

                # Add flow for this target node
                try:
                    sp = nx.shortest_path(graph, snode, tnode)
                    nexthop = sp[1]
                    ssid = self.get_sid(snode)
                    srctp = graph[snode][nexthop]['source-tp']
                    if nexthop == tnode:
                        php = True
                    else:
                        php = False
                    flow = {
                        'flow_id': 'flow:{}'.format(ssid),
                        'switch_id': snode,
                        'label': '{}'.format(ssid),
                        'port': srctp,
                        'penultimate': php
                    }
                    logging.debug("add_flow: {}".format(flow))
                    self.srm.add_flow(flow=flow)

                except nx.NetworkXNoPath:
                    logging.error("no path for {} to {}".format(snode, tnode))
        
    def del_all_flows(self, graph):
        '''Delete all flows in a graph'''

        for node in graph:
            self.srm.delete_flows(node)
            self.srm.delete_goto_sr_flow(node)

    def get_sid(self, ofid):
        '''get the sid from the openflow id'''
        id = int(ofid[ofid.index(':')+1:])
        return self.srgb_start + id

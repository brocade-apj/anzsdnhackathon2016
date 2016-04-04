import json
import networkx as nx
import sys
import os
import tm
import logging
import client

# Setup logging
#logging.basicConfig(filename='sr.log',level=logging.DEBUG)

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
        self.graph = nx.DiGraph()

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

        logging.debug("Get topology")

        # Allocate new graph
        g = nx.DiGraph()

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

    def add_sr_flow(self, graph, snode, tnode, nnode):
        '''Add an SR Flow to a node'''

        logging.debug("Add SR Flow {}:{}:{}".format(snode, tnode, nnode))

        tsid = self.get_sid(tnode)
        srctp = graph[snode][nnode]['source-tp']
        if nnode == tnode:
            php = True
        else:
            php = False
        flow = {
            'flow_id': 'flow:{}'.format(tsid),
            'switch_id': snode,
            'label': '{}'.format(tsid),
            'port': srctp,
            'penultimate': php
        }
        logging.debug("add_flow: {}".format(flow))
        self.srm.add_flow(flow=flow)

    def add_sr_flows_for_node(self, graph, snode):
        '''add sr flows for a node'''

        logging.debug("Adding SR flows for " + snode)

        # Add low priority goto to SR flow
        self.srm.add_goto_sr_flow(snode)

        for tnode in graph:
                # add rule for every other node (i.e. not us)
                if snode == tnode:
                    continue

                # Add flow for this target node
                try:
                    sp = nx.shortest_path(graph, snode, tnode)
                    self.add_sr_flow(graph, snode, tnode, sp[1])

                except nx.NetworkXNoPath:
                    logging.error("no path for {} to {}".format(snode, tnode))

    def add_sr_flows(self, graph):
        '''add sr flows'''
                
        logging.debug("Add SR Flows")

        # Spin thru each node and set the flows
        logging.debug("Adding flows for each node")
        for snode in graph:
            self.add_sr_flows_for_node(graph, snode)
        
    def del_sr_flow(self, node, tnode):
        '''delete sr flow'''

        logging.debug("Delete SR flow {}:{}".format(node,tnode))

        tsid = self.get_sid(tnode)
        flow_id = 'flow:{}'.format(tsid)
        logging.debug("deleting flow "+flow_id)
        self.srm.delete_flow(node, flow_id)

    def del_sr_flows_for_node(self, graph, snode):
        '''delete sr flows for a node'''

        logging.debug("Deleting flows for " + snode)

        # Delete low priority goto to SR flow
        self.srm.del_goto_sr_flow(snode)

        # Delete all node SIDs flows
        for tnode in graph:
                # del rule for every other node (i.e. not us)
                if snode == tnode:
                    continue

                # Delete flow for this target node
                self.del_sr_flow(graph, snode, tnode)

    def del_sr_flows(self, graph):
        '''delete all sr flows that we know of'''
                
        logging.debug("Delete SR flows")

        # Spin thru each node and del the flows
        logging.debug("Delete flows for each node")
        for snode in graph:
            del_sr_flows_for_node(graph, snode)
        
    def del_all_flows(self, graph):
        '''Delete all flows in a graph'''

        logging.debug("Delete All flows")

        for node in graph:
            self.srm.delete_flows(node)
            self.srm.delete_goto_sr_flow(node)

    def listen_to_topology(self):
        ws = self.srm.get_topology_stream()
        logging.info("Listening on stream for topology change... (ctrl-c to exit)")
        result =  ws.recv()
        logging.info("Change detected, new topology: ")

    def topology_equal(self, g1, g2):
        '''test if two graphs are the same'''

        for n in g1:
            if n in g2:
                for l in g1[n]:
                    if l in g2[n]:
                        if g1[n][l] != g2[n][l]:
                            return False
                    else:
                        return False
            else:
                return False

        return True

    def update_sr_flows(self, old):
        '''update flows with new graph'''

        logging.debug("Updating SR flows")

        # grab new flows
        new = self.get_topology()

        # Spin through nodes in the old topology
        for n in old:

            # Does the node exist in the new topology
            if n in new:

                # Spin through new targets
                for tnode in new:

                    # don't do ourselves
                    if n == tnode:
                        continue

                    # Check if spf of old is same as spf of the new topology
                    try:
                        old_nexthop = nx.shortest_path(old, n, tnode)[1]
                    except nx.NetworkXNoPath:
                        self.del_sr_flow(n, tnode)
                        continue
                    try:
                        new_nexthop = nx.shortest_path(new, n, tnode)[1]
                        if old_nexthop != new_nexthop:
                            self.add_sr_flow(new, n, tnode, new_nexthop)
                        else:
                            logging.debug("path from {} to {} already exists".format(n, tnode))

                    except nx.NetworkXNoPath:
                        self.add_sr_flow(new, n, tnode, new_nexthop)
                        logging.error("no path for {} to {}".format(snode, tnode))
            # node doesn't exist in the new topology
            else:
                logging.debug("old node {} gone away".format(n))

        # need to check for new nodes
        for n in new:
            if n not in old:
                self.add_sr_flows_for_node(graph, n)

        # return new topology
        return new

    def get_sid(self, ofid):
        '''get the sid from the openflow id'''

        id = int(ofid[ofid.index(':')+1:])
        return self.srgb_start + id


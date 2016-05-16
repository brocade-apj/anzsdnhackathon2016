# ANZ SDN Hacktathon 2016

This repository contains the result of [ANZ SDN Hackathon](http://www.anzsdn.net/index.php/event/sdn-demofest-and-hackathon/) performed by a 4 people Brocade team.

The current solution was developed in around 12 hours plus 30 minutes of presentation.

## Description

The purpose of the solution is to provide a Segment Routing network using OpenFlow switches and a SDN controller such as OpenDaylight.


## About Segment Routing

Segment Routing uses source routing paradigm, paths are configured in ingress nodes pushing a stack of labels, meaning each path is already pre-established on the ingress node. The engine that configures this path is aware of the network topology and it has the capability to optimise network behaviour changing paths on ingress nodes.

Each network device contains an id called Node Segmentation ID. All nodes in the network know how to reach the rest of the nodes taking  ECMP (equal cost multi-path) path.

The stack of labels configured on ingress node could be as simple as pushing one label with destination node. In this case, the path will take the shortest path. 

A path defined by the stack of labels can contain just destination, or waypoints plus destination or full list of nodes.

There are many other features around Segment Routing deeply described on the net.


## Architecture

The solution contains a python library to handle both Segment Routing configuration and service configuration plus a web interface and REST API built on [Flask](http://flask.pocoo.org/). 

It has been fully implemented external to OpenDaylight and it only uses OpenDaylight REST API to discover and program the network.

### Segment Routing module

This module reads the OpenFlow topology exposed by OpenDaylight on `http://ip:port/restconf/operational/network-topology:network-topology/topology/flow:1` and creates a graph based on the Dijkstra algorithm. 

For each node, it calculates the shortest path to the rest of nodes and installs a flow which matches on the Node Segmentation ID and delivers the packet to the calculated port. If it is the penultimate hop it will also pop the label.

If the topology changes it then reconfigures the OpenFlow network. For example, if a link goes down all the packets using that link will fail until this module reconfigures the OpenFlow devices. Fast reroute is not provided and this feature can also achieved using OpenFlow groups.

For simplification, the solution assumes that OpenFlow dpid is the Node Segmentation ID.


### Service module

Service module configures both ingress and egress node. It uses a MPLS service label to classify the traffic and apply actions like pushing a new VLAN or delivering the packet in a specific port.

It will install two flows, one on the ingress node which will mainly push all the labels both service and transport labels. And another one in the egress node to pop the service label, apply optional actions and deliver the packet to the desired port.

The default implementation of OpenFlow MPLS does not fully encapsulate the header and it just adds a shim header. Ethernet type is lost on ingress and recovered on egress node on the latest pop MPLS action.

If the service configured on ingress uses more than one ethernet type ( for example, a ping relies on ARP and IP) then it is required to create a service label per ethernet type to be able to recover the proper ethernet type on egress.


### Web UI

The UI provides a web interface which expose the capabilities of the service module. It provides the ability to configure an ingress switch, egress switch, waypoints and some classifiers.

## Usage

The solution comes with two main commands.

**sr** command exposes following operations to manage both segment routing and service flows.

```
$ ./sr -h
usage: srmanager [-h] [-C <path>] <command> [<args>]
(type 'srmanager -h' for details)

Available commands are:

   get-flow              Get flows
   add-flow              Add a flow
   del-flows             Delete all flows
   del-flow              Delete a flow
   add-service           Add a service
   del-service           Delete a service
   add-goto-sr           Add a default flow goto sr table
   del-goto-sr           Delete default flow goto sr table

```


**sr_daemon.py** starts a process which listen to the topology and configures the segment routing flows.

Following environment variables are used for both commands to provide OpenDaylight REST API connection details.

* `BSC_IP`: Opendaylight ip address, default 127.0.0.1
* `BSC_PORT`: REST API port, default 8181
* `BSC_USER`: REST API user, default admin
* `BSC_PASSWORD`: REST API password, default admin








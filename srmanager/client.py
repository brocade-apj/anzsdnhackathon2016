import os
import json
import requests
import xmltodict
import sr
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, Timeout

from srmanager.controller import Controller

class SrManagerClientException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

FLOW_SERVICE_PRIORITY=1000
FLOW_SR_PRIORITY=2000
FLOW_GO_TO_SR_PRIORITY=100

#-------------------------------------------------------------------------------
# Class 'Client'
#-------------------------------------------------------------------------------
class Client():
    """ Class that represents a Srmanager service """

    def __init__(self, **kwargs):
        """Initializes this object properties."""
        self.ctrl = Controller(**kwargs)

    def __str__(self):
        """ Returns string representation of this object. """
        return str(vars(self))

    def to_string(self):
        """ Returns string representation of this object. """
        return __str__()

    def to_json(self):
        """ Returns JSON representation of this object. """
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True,
                          indent=4)

    def brief_json(self):
        """ Returns JSON representation of this object (brief info). """
        d = {}
        return json.dumps(d, default=lambda o: o.__dict__, sort_keys=True,
                          indent=4)

    def get_flows(self,name):
        """ get flows from Segment Routing Manager """
        resp = self.ctrl.http_get_request(
                   self.ctrl.get_config_url()
                        + "/opendaylight-inventory:nodes/node/{}/table/1".format(name))

        if resp is not None:
            if resp.status_code == 200:
                flows = json.loads(resp.content)
                r=[]
                if ('flow-node-inventory:table' in flows
                    and len(flows['flow-node-inventory:table']) >0
                    and 'flow' in flows['flow-node-inventory:table'][0]):

                    for flow in flows['flow-node-inventory:table'][0]['flow']:
                        if is_sr_flow(flow['id']):
                            r.append(transfor_flow_sr(name,flow))
                return r
        return None

    def get_flow(self, name, id):
        """ Get a Segment Routing Manager flow given the switch name and id

        @param name: switch name to get
        @return: response keywords (see add_flow for description)

        """

        resp = self.ctrl.http_get_request(
                   self.ctrl.get_config_url()
                   + "/opendaylight-inventory:nodes/node/{}/table/1/flow/{}".format(name,id))

        if resp is not None:
            if resp.status_code == 200:
                flows = json.loads(resp.content)
                if ('flow-node-inventory:flow' in flows
                        and len(flows['flow-node-inventory:flow'])>0
                    ):

                    if is_sr_flow(flows['flow-node-inventory:flow'][0]['id']):
                        return transfor_flow_sr(name,flows['flow-node-inventory:flow'][0])
        return None

    def add_goto_sr_flow(self, name):
        """ Add go to table 1 to process sr rules

        @param name: switch name to get
        @return: response keywords (see add_flow for description)

        """

        id = "srgoto-table-1"

        payload = { "flow-node-inventory:flow": [
                    {
                        "id": id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": FLOW_GO_TO_SR_PRIORITY,
                        "idle-timeout": 0,
                        "instructions": {
                            "instruction": [
                                {
                                    "order":0,
                                    "go-to-table":{
                                        "table_id":1
                                    }
                                }
                            ]
                        },
                        "match": {
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 34887
                                }
                            }
                        }
                    }
                ]
            }

        resp = self.ctrl.http_put_request(
                 self.ctrl.get_config_url()+
                 "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(name,id)
                 ,json.dumps(payload))

        # Check response
        if resp is not None:
            if (resp.status_code == 200):
                return self.get_flow(name,id)

        return None


    def add_flow(self, **kwargs):
        """ Add or create a flow via Segment Routing Manager.

        @param name: switch name
        @param label: mpls label number
        @param port: port name
        @param penultimate: true/false
        @return: returns a resp dict (See below)

        Path Keywords:
        required:
          'name': 'name of this flow'
          'label': mpls label
          'port' : output port
          'penultimate': true/false

        Response Dict:
          'flow': new flow created

        """

        # Make call to Segment Routing Manager
        name = kwargs['flow']['switch_id']

        label = kwargs['flow']['label']
        port = kwargs['flow']['port']
        penultimate = kwargs['flow']['penultimate']

        if 'id' in kwargs['flow']:
            id = "src-" + id
        else:
            id = "sra-" + name + "-" + str(port) + "-" + str(label)


        payload = { "flow-node-inventory:flow": [
                    {
                        "id": id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": FLOW_SR_PRIORITY,
                        "idle-timeout": 0,
                        "instructions": {
                            "instruction": [
                                {
                                    "order": 0,
                                    "apply-actions": {
                                        "action": [
                                          {
                                            "order": 2,
                                            "output-action": {
                                              "output-node-connector": port
                                            }
                                          }
                                        ]
                                    }
                                }
                            ]
                        },
                        "match": {
                            "protocol-match-fields": {
                                "mpls-label": label
                            },
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 34887
                                }
                            }
                        }
                    }
                ]
            }

        if (penultimate is not None
            and (
                (type(penultimate) is bool and penultimate)
                or (type(penultimate) is not bool and unicode(penultimate) != u'false'))):
            payload['flow-node-inventory:flow'][0]['instructions']['instruction'][0]['apply-actions']['action'].append(
                    {
                      "order": 0,
                      "pop-mpls-action": {
                        "ethernet-type": 34887
                      }
                    }
                    )

        resp = self.ctrl.http_put_request(
                 self.ctrl.get_config_url()+
                 "/opendaylight-inventory:nodes/node/{}/table/1/flow/{}".format(name,id)
                 ,json.dumps(payload))

        # Check response
        if resp is not None:
            if (resp.status_code == 200):
                return self.get_flow(name,id)

        return None


    def delete_flow(self,name,id):
        """ Delete a flow via Segment Routing Manager.

        @param name: name of switch name
        @param id: id of flow to delete
        @return: response keywords (see add_flow for description)

        """

        resp = self.ctrl.http_delete_request(
                   self.ctrl.get_config_url()+
                   "/opendaylight-inventory:nodes/node/{}/table/1/flow/{}".format(name,id))

        return self.get_flow(name,id)

    def delete_flows(self,name):
        """ Delete all flows via Segment Routing Manager.

        @param name: name of switch name to delete switches
        @return: response keywords (see add_flow for description)

        """

        flows = self.get_flows(name)
        if flows is not None:
            for flow in flows:
                self.delete_flow(name, flow['id'])

        return None


    def add_service(self, **kwargs):
        """ Add or create a flow via Segment Routing Manager.

        @param id: ingress switch name
        @param ingress_switch: ingress switch name
        @param ingress_port: ingress port
        @param egress_switch: egress switch name
        @param egress_port: egress port
        @param ip_label: ip label
        @param arp_label: arp label
        @param waypoints: list of waypoints

        """

        sid = sr.SID()

        ingress_switch = kwargs['service']['ingress_switch']
        if not ingress_switch.startswith("openflow:"):
            ingress_switch="openflow:"+ingress_switch

        ingress_port = kwargs['service']['ingress_port']
        if ingress_port.startswith(ingress_switch):
            ingress_port=ingress_port.replace(ingress_switch,"")
        #if not ingress_port.startswith("openflow:"):
        #    ingress_port=ingress_switch+":"ingress_port

        egress_switch = kwargs['service']['egress_switch']
        if not egress_switch.startswith("openflow:"):
            egress_switch="openflow:"+egress_switch

        egress_port = kwargs['service']['egress_port']
        if not egress_port.startswith("openflow:"):
            egress_port=egress_switch+":"+egress_port

        ip_label = 1001
        if 'ip_label' in kwargs['service']:
            ip_label = kwargs['service']['ip_label']

        arp_label =1002
        if 'arp_label' in kwargs['service']:
            arp_label = kwargs['service']['arp_label']

        waypoints = []
        if 'waypoints' in kwargs['service']:
            waypoints = kwargs['service']['waypoints']

        id = "service-" + ingress_switch + ":" + ingress_port + "-" + egress_port
        ip_id = id +"-ip"
        arp_id = id +"-arp"

        ingress_ip = { "flow-node-inventory:flow": [
                    {
                        "id": ip_id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": FLOW_SERVICE_PRIORITY,
                        "idle-timeout": 0,
                        "instructions": {
                            "instruction": [
                                {
                                    "order": 0,
                                    "apply-actions": {
                                        "action": [
                                            {
                                                "order": 0,
                                                "push-mpls-action": {
                                                    "ethernet-type": 34887
                                                }
                                            },
                                            {
                                                "order": 1,
                                                "set-field": {
                                                    "protocol-match-fields": {
                                                        "mpls-label": ip_label
                                                    }
                                                }
                                            },
                                            {
                                                "order": 2,
                                                "push-mpls-action": {
                                                    "ethernet-type": 34887
                                                }
                                            },
                                            {
                                                "order": 3,
                                                "set-field": {
                                                    "protocol-match-fields": {
                                                        "mpls-label": sid.get_sid(egress_switch)
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "order":1,
                                    "go-to-table":{
                                        "table_id":1
                                    }
                                }
                            ]
                        },
                        "match": {
                            "in-port": "1",
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2048
                                }
                            }
                        }
                    }
                ]
            }

        ingress_arp = { "flow-node-inventory:flow": [
                    {
                        "id": arp_id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": FLOW_SERVICE_PRIORITY,
                        "idle-timeout": 0,
                        "instructions": {
                            "instruction": [
                                {
                                    "order": 0,
                                    "apply-actions": {
                                        "action": [
                                            {
                                                "order": 0,
                                                "push-mpls-action": {
                                                    "ethernet-type": 34887
                                                }
                                            },
                                            {
                                                "order": 1,
                                                "set-field": {
                                                    "protocol-match-fields": {
                                                        "mpls-label": arp_label
                                                    }
                                                }
                                            },
                                            {
                                                "order": 2,
                                                "push-mpls-action": {
                                                    "ethernet-type": 34887
                                                }
                                            },
                                            {
                                                "order": 3,
                                                "set-field": {
                                                    "protocol-match-fields": {
                                                        "mpls-label": sid.get_sid(egress_switch)
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "order":1,
                                    "go-to-table":{
                                        "table_id":1
                                    }
                                }
                            ]
                        },
                        "match": {
                            "in-port": "1",
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2054
                                }
                            }
                        }
                    }
                ]
            }

        order_action=4

        ## Add waypoints
        for waypoint in reversed(waypoints):
            if waypoint.startswith("openflow:"):
                waypoint=sid.get_sid(waypoint)

            order_action = order_action + 1
            push_mpls = {
                "order": order_action,
                "push-mpls-action": {
                    "ethernet-type": 34887
                }
            }
            ingress_ip['flow-node-inventory:flow'][0]['instructions']['instruction'][0]['apply-actions']['action'].append(push_mpls)
            ingress_arp['flow-node-inventory:flow'][0]['instructions']['instruction'][0]['apply-actions']['action'].append(push_mpls)

            order_action = order_action + 1
            set_mpls = {
                "order": order_action,
                "set-field": {
                    "protocol-match-fields": {
                        "mpls-label": waypoint
                    }
                }
            }
            ingress_ip['flow-node-inventory:flow'][0]['instructions']['instruction'][0]['apply-actions']['action'].append(set_mpls)
            ingress_arp['flow-node-inventory:flow'][0]['instructions']['instruction'][0]['apply-actions']['action'].append(set_mpls)


        egress_ip = { "flow-node-inventory:flow": [
                    {
                        "id": ip_id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": FLOW_SERVICE_PRIORITY,
                        "idle-timeout": 0,
                        "instructions": {
                            "instruction": [
                                {
                                    "order": 0,
                                    "apply-actions": {
                                        "action": [
                                          {
                                            "order": 0,
                                            "pop-mpls-action": {
                                              "ethernet-type": 2048
                                            }
                                          },
                                          {
                                              "order": 1,
                                              "output-action": {
                                                  "output-node-connector": egress_port
                                              }
                                          }
                                        ]
                                    }
                                }
                            ]
                        },
                        "match": {
                            "protocol-match-fields": {
                                "mpls-label": ip_label
                            },
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 34887
                                }
                            }
                        }
                    }
                ]
            }

        egress_arp = { "flow-node-inventory:flow": [
                    {
                        "id": arp_id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": FLOW_SERVICE_PRIORITY,
                        "idle-timeout": 0,
                        "instructions": {
                            "instruction": [
                                {
                                    "order": 0,
                                    "apply-actions": {
                                        "action": [
                                          {
                                            "order": 0,
                                            "pop-mpls-action": {
                                              "ethernet-type": 2054
                                            }
                                          },
                                          {
                                              "order": 1,
                                              "output-action": {
                                                  "output-node-connector": egress_port
                                              }
                                          }
                                        ]
                                    }
                                }
                            ]
                        },
                        "match": {
                            "protocol-match-fields": {
                                "mpls-label": arp_label
                            },
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 34887
                                }
                            }
                        }
                    }
                ]
            }

        resp = self.ctrl.http_put_request(
                 self.ctrl.get_config_url()+
                 "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(ingress_switch,ip_id)
                 ,json.dumps(ingress_ip))
        if resp.status_code != 200:
            print resp.content

        resp = self.ctrl.http_put_request(
                 self.ctrl.get_config_url()+
                 "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(ingress_switch,arp_id)
                 ,json.dumps(ingress_arp))
        if resp.status_code != 200:
            print resp.content

        resp = self.ctrl.http_put_request(
                 self.ctrl.get_config_url()+
                 "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(egress_switch,ip_id)
                 ,json.dumps(egress_ip))
        if resp.status_code != 200:
            print resp.content

        resp = self.ctrl.http_put_request(
                 self.ctrl.get_config_url()+
                 "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(egress_switch,arp_id)
                 ,json.dumps(egress_arp))
        if resp.status_code != 200:
            print resp.content

        return None


    def delete_service(self,**kwargs):
        """ Delete a flow via Segment Routing Manager.

        @param name: name of switch name
        @param id: id of flow to delete
        @return: response keywords (see add_flow for description)

        """

        ingress_switch = kwargs['service']['ingress_switch']
        if not ingress_switch.startswith("openflow:"):
            ingress_switch="openflow:"+ingress_switch

        ingress_port = kwargs['service']['ingress_port']
        if ingress_port.startswith(ingress_switch):
            ingress_port=ingress_port.replace(ingress_switch,"")
        #if not ingress_port.startswith("openflow:"):
        #    ingress_port=ingress_switch+":"ingress_port

        egress_switch = kwargs['service']['egress_switch']
        if not egress_switch.startswith("openflow:"):
            egress_switch="openflow:"+egress_switch

        egress_port = kwargs['service']['egress_port']
        if not egress_port.startswith("openflow:"):
            egress_port=egress_switch+":"+egress_port


        id = "service-" + ingress_switch + ":" + ingress_port + "-" + egress_port
        ip_id = id +"-ip"
        arp_id = id +"-arp"

        self.ctrl.http_delete_request(
                   self.ctrl.get_config_url()+
                   "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(ingress_switch,ip_id))

        self.ctrl.http_delete_request(
                   self.ctrl.get_config_url()+
                   "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(ingress_switch,arp_id))

        self.ctrl.http_delete_request(
                   self.ctrl.get_config_url()+
                   "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(egress_switch,ip_id))

        self.ctrl.http_delete_request(
                   self.ctrl.get_config_url()+
                   "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(egress_switch,arp_id))


def is_sr_flow(id):
    if id is not None and id.startswith('sr'):
        return True
    return False

def transfor_flow_sr(name,flow):
    r = {
        'id':flow['id'],
        'name': name
    }

    ## if we receive the id given by the user
    ## return the id as given by the client
    if r['id'].startswith("src-"):
        r['id'] = r['id'].replace("src-","")

    if ('match' in flow
        and 'protocol-match-fields' in flow['match']
        and 'mpls-label' in flow['match']['protocol-match-fields']
        ):
        r['label']=flow['match']['protocol-match-fields']['mpls-label']

    if ('instructions' in flow
        and 'instruction' in flow['instructions']
        and len(flow['instructions']['instruction']) > 0
        and 'apply-actions' in flow['instructions']['instruction'][0]
        and 'action' in flow['instructions']['instruction'][0]['apply-actions']
        and len(flow['instructions']['instruction'][0]['apply-actions']['action'])>0
        ):
        for action in flow['instructions']['instruction'][0]['apply-actions']['action']:
            if 'pop-mpls-action' in action:
                r['penultimate']=True

    return r

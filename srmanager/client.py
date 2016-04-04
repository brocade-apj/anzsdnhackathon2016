import os
import json
import requests
import xmltodict

from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, Timeout

from srmanager.controller import Controller

class SrManagerClientException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

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
                        + "/opendaylight-inventory:nodes/node/{}/table/0".format(name))

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
                   + "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(name,id))

        if resp is not None:
            if resp.status_code == 200:
                flows = json.loads(resp.content)
                if ('flow-node-inventory:flow' in flows
                        and len(flows['flow-node-inventory:flow'])>0
                    ):

                    if is_sr_flow(flows['flow-node-inventory:flow'][0]['id']):
                        return transfor_flow_sr(name,flows['flow-node-inventory:flow'][0])
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
        name = kwargs['flow']['name']
        label = kwargs['flow']['label']
        port = kwargs['flow']['port']
        penultimate = kwargs['flow']['penultimate']

        id = "sr-" + name + "-" + port + "-" + label

        payload = { "flow-node-inventory:flow": [
                    {
                        "id": id,
                        "table_id": 0,
                        "hard-timeout": 0,
                        "priority": 32767,
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
                 "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(name,id)
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
                   "/opendaylight-inventory:nodes/node/{}/table/0/flow/{}".format(name,id))

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


def is_sr_flow(id):
    if id is not None and id.startswith('sr'):
        return True
    return False

def transfor_flow_sr(name,flow):
    r = {
        'id':flow['id'],
        'name': name
    }

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

import os
import json
import logging
import argparse
import requests
import xmltodict

from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, Timeout


LOG = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# Class 'Controller'
#-------------------------------------------------------------------------------
class Controller():
    """ Class that represents a Controller device. """

    def __init__(self, **kwargs):
        """Initializes this object properties."""

        if not kwargs.get('config'):
            raise Exception('controller needs config properties')

        # Check the config (and supply defaults)
        self.config = self.check_config(kwargs['config'])

        self.default_headers = {
            'content-type': 'application/json', 'accept': 'application/json'}

    def check_config(self, cfg):
        """Check properties and supply defaults."""

        req_props = ['ip', 'port', 'username', 'password']

        # defaults
        props = { 'protocol': 'http', 'timeout': 30 }

        for prop in req_props:
            if prop not in cfg:
                raise Exception('can\'t find property {0}'.format(prop))

        # Update defaults with given props
        props.update(cfg)

        return props

    def __str__(self):
        """ Returns string representation of this object. """
        return str(vars(self))

    def to_string(self):
        """ Returns string representation of this object. """
        return self.__str__()

    def to_json(self):
        """ Returns JSON representation of this object. """
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True,
                          indent=4)

    def brief_json(self):
        """ Returns JSON representation of this object (brief info). """
        d = {'protocol': self.protocol,
             'ipAddr': self.config['ip'],
             'portNum': self.config['port'],
             'adminName': self.config['username'],
             'adminPassword': self.config['password']}
        return json.dumps(d, default=lambda o: o.__dict__, sort_keys=True,
                          indent=4)

    def http_get_request(self, url, headers=None, timeout=None):
        """ Sends HTTP GET request to a remote server
            and returns the response.

        :param string url: The complete url including protocol:
                           http://www.example.com/path/to/resource
        :param string data: The data to include in the body of the request.
                            Typically set to None.
        :param dict headers: The headers to include in the request.
        :param string timeout: Pass a timeout for longlived queries
        :return: The response from the http request.
        :rtype: None or `requests.response`
            <http://docs.python-requests.org/en/latest/api/#requests.Response>

        """

        if headers is None:
            headers = self.default_headers

        resp = None
        if timeout is None:
            timeout = self.config['timeout']

        resp = requests.get(url,
                                auth=HTTPBasicAuth(self.config['username'],
                                                   self.config['password']),
                                data=None, headers=headers,
                                timeout=timeout)
        if resp is not None:
            if resp.status_code == 200:
                LOG.debug("found {}".format(url))
            elif resp.status_code == 404:
                LOG.debug("not found {}".format(url))
            else:
                LOG.error("error getting {} message {}".format(url,resp.content))


        return (resp)

    def http_post_request(self, url, data, headers=None):
        """ Sends HTTP POST request to a remote server
            and returns the response.

        :param string url: The complete url including protocol:
                           http://www.example.com/path/to/resource
        :param string data: The data to include in the body of the request.
                            Typically set to None.
        :param dict headers: The headers to include in the request.
        :return: The response from the http request.
        :rtype: None or `requests.response`
            <http://docs.python-requests.org/en/latest/api/#requests.Response>

        """

        if headers is None:
            headers = self.default_headers

        resp = None

        resp = requests.post(url,
                                 auth=HTTPBasicAuth(self.config['username'],
                                                    self.config['password']),
                                 data=data, headers=headers,
                                 timeout=self.config['timeout'])

        if resp is not None:
            if resp.status_code == 204:
                LOG.debug("added {} {}".format(url,data))
            else:
                LOG.error("error posting {} data {} message {}".format(url,data,resp.content))

        return (resp)

    def http_put_request(self, url, data, headers=None):
        """ Sends HTTP PUT request to a remote server
            and returns the response.

        :param string url: The complete url including protocol:
                           http://www.example.com/path/to/resource
        :param string data: The data to include in the body of the request.
                            Typically set to None.
        :param dict headers: The headers to include in the request.
        :return: The response from the http request.
        :rtype: None or `requests.response`
            <http://docs.python-requests.org/en/latest/api/#requests.Response>

        """

        if headers is None:
            headers = self.default_headers

        resp = None

        resp = requests.put(url,
                                auth=HTTPBasicAuth(self.config['username'],
                                                   self.config['password']),
                                data=data, headers=headers,
                                timeout=self.config['timeout'])

        if resp is not None:
            if resp.status_code == 200:
                LOG.debug("added {} {}".format(url,data))
            else:
                LOG.error("error posting {} data {} message {}".format(url,data,resp.content))

        return (resp)

    def http_delete_request(self, url, data=None, headers=None):
        """ Sends HTTP DELETE request to a remote server
            and returns the response.

        :param string url: The complete url including protocol:
                           http://www.example.com/path/to/resource
        :param string data: The data to include in the body of the request.
                            Typically set to None.
        :param dict headers: The headers to include in the request.
        :return: The response from the http request.
        :rtype: None or `requests.response`
            <http://docs.python-requests.org/en/latest/api/#requests.Response>

        """

        if headers is None:
            headers = self.default_headers

        resp = None

        resp = requests.delete(url,
                                   auth=HTTPBasicAuth(self.config['username'],
                                                      self.config['password']),
                                   data=data, headers=headers,
                                   timeout=self.config['timeout'])

        if resp is not None:
            if resp.status_code == 200:
                LOG.debug("delete {}".format(url))
            elif resp.status_code == 404:
                LOG.debug("delete {}".format(url))
            else:
                LOG.error("error posting {} message {}".format(url,resp.content))
        return (resp)

    def get_base_url(self):
        return  ("{}://{}:{}/restconf").format(
            self.config['protocol'],self.config['ip'], self.config['port'])

    def get_operational_url(self):
        return self.get_base_url() + "/operational"

    def get_config_url(self):
        return self.get_base_url() + "/config"



    def create_topology_stream(self):
        # This calls RESTConf api to create a stream for notifications about changes
        #     in the topology in the operational data store
        # RETURNS: stream's url or None if fail
        url = self.get_base_url() + '/operations/sal-remote:create-data-change-event-subscription'

        headers = {'content-type': 'application/xml',
                    'accept': 'application/json'}

        payload = '<input xmlns="urn:opendaylight:params:xml:ns:yang:controller:md:sal:remote"> \
                        <path xmlns:a="urn:TBD:params:xml:ns:yang:network-topology">/a:network-topology</path> \
                        <datastore xmlns="urn:sal:restconf:event:subscription">OPERATIONAL</datastore> \
                        <scope xmlns="urn:sal:restconf:event:subscription">SUBTREE</scope> \
                    </input>'

        r = requests.post(url, data=payload, headers=headers, auth=HTTPBasicAuth(self.config['username'], self.config['password']))

        streamName = r.text
        #print streamName

        if ('error' in streamName):
            print "Error: " + streamName
            return None
        else:
            streamName = r.json()
            streamName = streamName['output']
            streamName = streamName['stream-name']
            return streamName

    def subcribe_stream(self,streamName):
        # This calls the RESTConf api to suscribe to the stream at streamName
        # INPUT:
        #    rConfBaseUrl - base url at which RestConf calls may be made - example:  http://192.168.56.101:8181/restconf
        #    user - the user name with which to authenticate - example: admin
        #    password - the password with which to authenticate - example - admin
        #    streamName - name of stream with which to subscribe (streamName is returned from creating it)
        # RETURNS: stream's url at which to listen with web socket
        url = self.get_base_url() + '/streams/stream/' + streamName
        #print url
        headers = {'content-type': 'application/json',
                    'accept': 'application/json'}
        r = requests.get(url, headers=headers, auth=HTTPBasicAuth(self.config['username'], self.config['password']))
        streamListenUrl = r.headers['location']
        return streamListenUrl

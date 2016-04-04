import os
import json
import argparse
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout
import xmltodict

from functools import wraps

from srmanager.client import Client
from srmanager.client import SrManagerClientException

#-------------------------------------------------------------------------------
# Class 'Shell'
#-------------------------------------------------------------------------------
class Shell(object):
    """ Segment Routing manager cli commands executer """

    def __init__(self):
        self.prog = 'srmanager'
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description='Segment Routing manager command line tool for interaction with OpenFlow Controller',
            usage="%(prog)s [-h] [-C <path>] <command> [<args>]\n"
                  "(type '%(prog)s -h' for details)\n"
                     "\nAvailable commands are:\n"
                     "\n   get-flow              Get flows"
                     "\n   add-flow              Add a flow"
                     "\n   del-flows             Delete all flows"
                     "\n   del-flow              Delete a flow"
                     "\n"
                     "\n  '%(prog)s help <command>' provides details for a specific command")

        parser.add_argument('-C', metavar="<path>", dest='ctrl_cfg_file',
                            help="path to the controller's configuration file (default is './ctrl.yml')",
                            default="./ctrl.yml")

        parser.add_argument('command', help='command to be executed')

        # following method will save on args the first argument
        # and re
        args, remaining_args = parser.parse_known_args()

        # Get Controller's attributes from configuration file
        self.config  = self.get_controller_config(args.ctrl_cfg_file)
        if (self.config == None):
            print "\n".strip()
            print ("Cannot find controller configuration file")
            print "\n".strip()
            exit(1)

        self.sr = Client(config=self.config)

        # Invoke method that is matching the name of sub-command argument
        # cmd variable contains the first argument
        cmd = args.command.replace('-', '_')

        if hasattr(self, cmd):
            getattr(self, cmd)(remaining_args)
        else:
            print "\n".strip()
            print ("Error, unrecognized command '%s'" % cmd)
            print "\n".strip()
            parser.print_help()
            exit(1)

    #---------------------------------------------------------------------------
    # decorators
    #---------------------------------------------------------------------------
    def connects(f):
        @wraps(f)
        def wrapper(*args, **kw):
            try:
                return f(*args, **kw)

            except ConnectionError, e:
                print('A connection error occured: {0}'.format(e))
                exit()
            except ConnectTimeout, e:
                print('A connect timeout occured: {0}'.format(e))
                exit()
            except SrManagerClientException, e:
                print('SrManager Client Error: {0}'.format(e))
                exit()


        return wrapper

    #---------------------------------------------------------------------------
    # get controller object given yaml configuration file
    #---------------------------------------------------------------------------
    def get_controller_config(self, file):
        props = {}

        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                props = yaml.load(f)

        config = {}
        config['ip']=get_property(props,'BSC_IP','127.0.0.1')
        config['port']=get_property(props,'BSC_PORT','8181')
        config['username']=get_property(props,'BSC_USER','admin')
        config['password']=get_property(props,'BSC_PASSWORD','admin')
        config['protocol']=get_property(props,'BSC_PROTOCOL','http')
        config['timeout']=get_property(props,'BSC_TIMEOUT', 5)

        return config


    #---------------------------------------------------------------------------
    # get flows
    #---------------------------------------------------------------------------
    @connects
    def get_flow(self, arguments):

        # parse agurments
        parser = argparse.ArgumentParser(
            prog=self.prog,
            usage="%(prog)s get-flow\n\n"
                  "Options:\n"
                  "  -n, --name          switch name\n"
                  "  -i, --id            flow id\n")
        parser.add_argument('-n', '--name', metavar = "<NAME>", required=True)
        parser.add_argument('-i', '--id', metavar = "<ID>", required=False)
        parser.add_argument('-U', action="store_true", dest="usage", help=argparse.SUPPRESS)

        args = parser.parse_args(arguments)
        if(args.usage):
            parser.print_usage()
            print "\n".strip()

        if args.id:
            result = self.sr.get_flow(args.name,args.id)
        else:
            result = self.sr.get_flows(args.name)

        if result is not None:
            print_json(result)
        else:
            print "no flows found"


    #---------------------------------------------------------------------------
    # get flows
    #---------------------------------------------------------------------------
    @connects
    def add_flow(self, arguments):

        # parse agurments
        parser = argparse.ArgumentParser(
            prog=self.prog,
            usage="%(prog)s add-flow\n\n"
                  "add a flow to sr manager\n\n"
                  "Options:\n"
                  "  -n, --name                         switch name (format: openflow:1)\n"
                  "  -p, --port                         port name (format: openflow:1:1)\n"
                  "  -l, --label                        mpls label number\n"
                  "  -u, --penultimate                  true/false if it is penultimate (optional)\n"
                  )
        parser.add_argument('-n', '--name', metavar = "<NAME>", required=True)
        parser.add_argument('-p', '--port', metavar = "<PORT>", required=True)
        parser.add_argument('-l', '--label', metavar = "<LABEL>", required=True)
        parser.add_argument('-u', '--penultimate', metavar = "<PENULTIMATE>", required=False)

        parser.add_argument('-U', action="store_true", dest="usage", help=argparse.SUPPRESS)

        args = parser.parse_args(arguments)
        if(args.usage):
            parser.print_usage()
            print "\n".strip()


        penultimate=False
        if args.penultimate:
            penultimate=True

        flow = {
            'name':args.name,
            'label':args.label,
            'port':args.port,
            'penultimate':args.penultimate,
        }
        result = self.sr.add_flow(flow=flow)

        flows = result.get('flows')
        if result is not None:
            print_json(result)
        else:
            print "flow not added"


    #---------------------------------------------------------------------------
    # delete flow
    #---------------------------------------------------------------------------
    @connects
    def del_flow(self, arguments):

        # parse agurments
        parser = argparse.ArgumentParser(
            prog=self.prog,
            usage="%(prog)s del-flow\n\n"
                  "Delete flow from switch name\n\n"
                  "Options:\n"
                  "  -n, --name          device name\n"
                  "  -i, --id            flow id\n")
        parser.add_argument('-n', '--name', metavar = "<NAME>", required=True)
        parser.add_argument('-i', '--id', metavar = "<ID>", required=True)
        parser.add_argument('-U', action="store_true", dest="usage", help=argparse.SUPPRESS)

        args = parser.parse_args(arguments)
        if(args.usage):
            parser.print_usage()
            print "\n".strip()


        result = self.sr.delete_flow(args.name,args.id)

        if result is None:
            print "flow {} removed from {}".format(args.id,args.name)
        else:
            print "flow {} not removed from {}".format(args.id,args.name)

    #---------------------------------------------------------------------------
    # delete flow
    #---------------------------------------------------------------------------
    @connects
    def del_flows(self, arguments):

        # parse agurments
        parser = argparse.ArgumentParser(
            prog=self.prog,
            usage="%(prog)s del-flows\n\n"
                  "Delete all flows from switch name\n\n"
                  "Options:\n"
                  "  -n, --name          device name\n")
        parser.add_argument('-n', '--name', metavar = "<NAME>", required=True)
        parser.add_argument('-U', action="store_true", dest="usage", help=argparse.SUPPRESS)

        args = parser.parse_args(arguments)
        if(args.usage):
            parser.print_usage()
            print "\n".strip()


        result = self.sr.delete_flows(args.name)

        if result is None:
            print "flows removed from {}".format(args.name)
        else:
            print "flows not removed from {}".format(args.name)


#-------------------------------------------------------------------------------
# common functions
#-------------------------------------------------------------------------------

def get_property(dic,name,default):
    if name in dic and dic[name] is not None:
        return dic[name]
    if name in os.environ and os.environ[name] is not None:
        return os.environ[name]

    return default

def print_json(result):
    print json.dumps(result, default=lambda o: o.__dict__, sort_keys=True, indent=4)

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    Shell()

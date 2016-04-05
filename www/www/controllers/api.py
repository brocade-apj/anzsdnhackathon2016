from flask import request
from flask_restful import reqparse, abort, Resource, Api
from www.extensions import mongo
from srmanager.client import Client
from bson.json_util import dumps
from bson.objectid import ObjectId


api = Api(prefix='/api/v1')  

class Service(Resource):
  def get(self, id):
    return {'hello': 'world'}

  def delete(self, id):
    print "We are trying to delete %s" % (id)
    services = mongo.db.services
    service_obj = services.find_one({'_id': ObjectId(id)})
    print service_obj

    service = {
      'ingress_switch': str(service_obj['ingress_switch']),
      'ingress_port': str(service_obj['ingress_port']),
      'egress_switch': str(service_obj['egress_switch']),
      'egress_port': str(service_obj['egress_port'])
    }

    print service

    services.delete_one({'_id': ObjectId(id)})

    srm = Client(config={'ip': '202.9.5.219', 'port': 8181, 'username': 'admin', 'password': 'admin'})
    srm.delete_service(service=service)

    return service, 204

class Services(Resource):
  def get(self):
    services = mongo.db.services
    return dumps(services.find().pretty())

  def post(self):
    parser = reqparse.RequestParser()
    parser.add_argument('ingress-switch', type=str)
    parser.add_argument('egress-switch', type=str)
    parser.add_argument('ingress-port', type=str)
    parser.add_argument('egress-port', type=str)

    json = request.get_json()

    args = parser.parse_args()

    service = {
      'ingress_switch': args['ingress-switch'],
      'ingress_port': args['ingress-port'],
      'egress_switch': args['egress-switch'],
      'egress_port': args['egress-port']
    }
    if json['waypoints']:
      service['waypoints'] = []
      for waypoint in json['waypoints']:
        service['waypoints'].append(str(waypoint))

    services = mongo.db.services
    db_id = services.insert_one(service).inserted_id

    srm = Client(config={'ip': '202.9.5.219', 'port': 8181, 'username': 'admin', 'password': 'admin'})
    
    print service
    
    srm.add_service(service=service)

    service['_id'] = str(service['_id'])
    return service, 201

api.add_resource(Services, '/services')
api.add_resource(Service, '/services/<id>')
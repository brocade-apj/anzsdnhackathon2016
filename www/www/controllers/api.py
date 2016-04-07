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
    services = mongo.db.services
    service_obj = services.find_one({'_id': ObjectId(id)})

    service = {
      'ingress_switch': str(service_obj['ingress_switch']),
      'ingress_port': str(service_obj['ingress_port']),
      'egress_switch': str(service_obj['egress_switch']),
      'egress_port': str(service_obj['egress_port'])
    }

    services.delete_one({'_id': ObjectId(id)})

    srm = Client(config={'ip': '127.0.0.1', 'port': 8181, 'username': 'admin', 'password': 'admin'})
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
    parser.add_argument('waypoints', type=list, location='json')

    args = parser.parse_args()

    service = {
      'ingress_switch': args['ingress-switch'],
      'ingress_port': args['ingress-port'],
      'egress_switch': args['egress-switch'],
      'egress_port': args['egress-port']
    }

    if args['waypoints']:
      service['waypoints'] = [str(waypoint) for waypoint in args['waypoints']]

    services = mongo.db.services
    db_id = services.insert_one(service).inserted_id

    srm = Client(config={'ip': '127.0.0.1', 'port': 8181, 'username': 'admin', 'password': 'admin'})

    srm.add_service(service=service)

    service['_id'] = str(service['_id'])
    return service, 201

api.add_resource(Services, '/services')
api.add_resource(Service, '/services/<id>')

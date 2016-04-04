from flask import request
from flask_restful import reqparse, abort, Resource, Api
from www.extensions import mongo
from srmanager.client import Client

api = Api(prefix='/api/v1')  

class Service(Resource):
  def get(self, id):
    return {'hello': 'world'}

  def delete(self, id):
    # Delete something
    return {'hello': 'world'}, 204

class Services(Resource):
  def get(self):
    return {'hello': 'world'}

  def post(self):
    parser = reqparse.RequestParser()
    parser.add_argument('ingress-switch')
    parser.add_argument('egress-switch')
    parser.add_argument('ingress-port')
    parser.add_argument('egress-port')
    parser.add_argument('waypoints')

    args = parser.parse_args()

    service = {
      'ingress_switch': args['ingress-switch'],
      'ingress_port': args['ingress-port'],
      'egress_switch': args['egress-switch'],
      'egress_port': args['egress-port']
    }
    if args['waypoints']:
      service['waypoints'] = args['waypoints']

    services = mongo.db.services
    db_id = services.insert_one(service).inserted_id

    srm = Client(config={'ip': '202.9.5.219', 'port': 8181, 'username': 'admin', 'password': 'admin'})
    print service
    srm.add_service(service=service)

    service['_id'] = str(service['_id'])
    return service, 201

api.add_resource(Services, '/services')
api.add_resource(Service, '/services/<id>')
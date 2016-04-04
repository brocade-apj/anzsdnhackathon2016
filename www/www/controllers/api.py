from flask import request
from flask_restful import reqparse, abort, Resource, Api

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
    request.form['data']
    return {'hello': 'world'}, 201

api.add_resource(Services, '/services')
api.add_resource(Service, '/services/<id>')
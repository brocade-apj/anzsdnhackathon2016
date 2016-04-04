#!/usr/bin/env python

import os

from flask.ext.script import Manager, Server
from flask.ext.script.commands import ShowUrls, Clean
from www import create_app
from www.extensions import mongo

# default to dev config because no one should use this in
# production anyway
env = os.environ.get('WWW_ENV', 'dev')
app = create_app('www.settings.%sConfig' % env.capitalize())

manager = Manager(app)
manager.add_command("server", Server())
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())


@manager.shell
def make_shell_context():
  """ Creates a python REPL with several default imports
      in the context of the app
  """

  return dict(app=app, mongo=mongo)

@manager.command
def create_db():
  if env == 'dev':
    tests_collection = mongo.db.tests
    test = [{'_id': 1, 'name':'darin'}, {'_id': 2, 'name':'jon'}]
    obj_ids = tests_collection.insert_many(test).inserted_ids
    return obj_ids

if __name__ == "__main__":
  manager.run()

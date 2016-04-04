from flask.ext.cache import Cache
from flask_assets import Environment
from flask.ext.pymongo import PyMongo
# Setup flask cache
cache = Cache()

# init flask assets
assets_env = Environment()

mongo = PyMongo()
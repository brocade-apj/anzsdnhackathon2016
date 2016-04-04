class Config(object):
    SECRET_KEY = 'secret key'

class ProdConfig(Config):
    ENV = 'prod'
    CACHE_TYPE = 'simple'


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'null'
    ASSETS_DEBUG = True

    MONGO_HOST = "192.168.99.100"
    MONGO_PORT = 32768
    MONGO_DBNAME = 'dev_sr'


class TestConfig(Config):
    ENV = 'test'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'null'
    WTF_CSRF_ENABLED = False

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    None
    # DEBUG = True #os.environ.get('DEBUG')
    # TESTING = True #os.environ.get('TESTING')
    # CSRF_ENABLED = True
    # AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    # AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
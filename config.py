import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'amaqykpts'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql://tonytong:950726@localhost/test'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

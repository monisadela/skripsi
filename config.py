import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/sayang'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


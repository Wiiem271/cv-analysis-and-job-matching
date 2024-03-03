from flask_mongoengine import MongoEngine
from mongoengine import *

db = MongoEngine()

def initialize_db(app):
   db.init_app(app)

# Déconnexion de la connexion existante
#db.disconnect()


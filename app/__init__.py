from flask import Flask

from app.webhook.routes import webhook
from app.extensions import init_mongo

# Creating our flask app
def create_app():

    app = Flask(__name__)
    init_mongo(app)

    app.register_blueprint(webhook)
    
    return app

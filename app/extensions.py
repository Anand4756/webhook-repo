from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv
load_dotenv()

# Setup MongoDB here
mongo = PyMongo()
def init_mongo(app):
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/database")
    app.config["MONGO_URI"] = mongo_uri

    mongo.init_app(app)
# Access the MongoDB collection

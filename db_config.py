import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

MONGO_URI = os.getenv('MONGO_DB_URI')
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_fallback_secret_key') # Provide a fallback

if not MONGO_URI:
    raise ValueError("No MONGO_DB_URI found in environment variables. Did you create a .env file?")
if not SECRET_KEY:
     raise ValueError("No FLASK_SECRET_KEY found in environment variables. Did you create a .env file?")

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database() # Gets the database name from the URI
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful.")
    users_collection = db.users # Or specify db['users']
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None
    db = None
    users_collection = None
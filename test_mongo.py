#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

print("Loading environment...")
# Load environment variables
load_dotenv()

print("Importing pymongo...")
try:
    from pymongo import MongoClient
    print("✅ PyMongo imported successfully")
except ImportError as e:
    print(f"❌ Failed to import pymongo: {e}")
    sys.exit(1)

# Test MongoDB connection
def test_mongo_connection():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found")
        return False
    
    print(f"Testing connection to: {mongodb_uri[:50]}...")
    
    try:
        # Test with direct pymongo client with timeout
        print("Creating MongoClient...")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        print("Getting default database...")
        # Test connection
        db = client.get_default_database()
        print(f"Default database name: {db.name}")
        
        print("Testing ping...")
        # Test ping
        result = db.command("ping")
        print(f"Ping result: {result}")
        
        print("Listing collections...")
        # List collections
        collections = db.list_collection_names()
        print(f"Existing collections: {collections}")
        
        print("✅ MongoDB connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            print("Closing client...")
            client.close()
        except:
            pass

if __name__ == "__main__":
    print("Starting MongoDB connection test...")
    test_mongo_connection()
    print("Test completed.")

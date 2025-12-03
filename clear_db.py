import os
from pymongo import MongoClient
from dotenv import load_dotenv

def clear_sessions_collection():
    """
    Connects to the MongoDB database and completely clears the 'sessions' collection.
    """
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "convosphere")

    print(f"Connecting to MongoDB at {mongo_uri}...")
    try:
        client = MongoClient(mongo_uri)
        db = client[mongo_db_name]
        sessions_collection = db["sessions"]

        print(f"Found {sessions_collection.count_documents({})} documents in the 'sessions' collection.")
        
        if sessions_collection.count_documents({}) > 0:
            print("Clearing the 'sessions' collection...")
            result = sessions_collection.delete_many({})
            print(f"Successfully deleted {result.deleted_count} documents.")
        else:
            print("Collection is already empty. Nothing to do.")

        client.close()
        print("Connection closed.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    clear_sessions_collection()

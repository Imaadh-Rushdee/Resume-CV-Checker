import os
from uuid import uuid4
from datetime import datetime
from pymongo import MongoClient
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Import generateUserToken from services.userService
from services import userService

# MongoDB setup
db_uri = os.getenv("DB_URL")
client = MongoClient(db_uri)
db = client["job_selector_db"]
users_col = db["users"]


def loginWithGoogle(google_token: str):
    """
    Logs in a user with Google OAuth token.
    If the user is new, create a record in users collection.
    Returns: {user_id, username, token} or None if invalid
    """
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(google_token, google_requests.Request())
        email = idinfo.get("email")
        name = idinfo.get("name")

        if not email:
            return None  # Invalid token

        # Check if user already exists
        user = users_col.find_one({"username": email})
        if not user:
            # First-time login → create user
            user_data = {
                "user_id": str(uuid4()),
                "username": email,
                "password": None,  # No password for Google users
                "role": "user",
                "name": name,
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            users_col.insert_one(user_data)
            user = user_data

        # Issue local JWT
        token = userService.generateUserToken(user["user_id"])
        return {"user_id": user["user_id"], "username": user["username"], "token": token}

    except ValueError:
        # Invalid token
        return None

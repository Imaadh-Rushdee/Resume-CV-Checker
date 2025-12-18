import os
from pymongo import MongoClient
from datetime import datetime
from uuid import uuid4

from utils import passwordHash, jwtUtility

# Google auth
from google.oauth2 import id_token
from google.auth.transport import requests

# ---------------- MongoDB Setup ----------------

db_uri = os.getenv("DB_URL")
client = MongoClient(db_uri)
db = client["job_selector_db"]
users_col = db["users"]

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# ---------------- User Service Layer ----------------

def getAllUsers():
    return list(users_col.find({}, {"_id": 0, "password": 0}))


def getUserById(user_id: str):
    return users_col.find_one(
        {"user_id": user_id},
        {"_id": 0, "password": 0}
    )


def getUserByRole(role: str):
    return list(users_col.find(
        {"role": {"$regex": role, "$options": "i"}},
        {"_id": 0, "password": 0}
    ))


def getUserByDateCreated(date: str):
    start = datetime.fromisoformat(date)
    end = start.replace(hour=23, minute=59, second=59)
    return list(users_col.find(
        {"created_at": {"$gte": start, "$lte": end}},
        {"_id": 0, "password": 0}
    ))


# ---------------- Local Registration ----------------

def addUser(username: str, password: str, role: str = "user"):
    if users_col.find_one({"username": username}):
        raise ValueError("Username already exists")

    user_data = {
        "user_id": str(uuid4()),
        "username": username,
        "password": passwordHash.hash_password(password),
        "role": role,
        "auth_provider": "local",
        "google_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": None
    }

    users_col.insert_one(user_data)
    return user_data["user_id"]


# ---------------- Update & Delete ----------------

def updateUser(user_id: str, data: dict):
    data["updated_at"] = datetime.utcnow()
    result = users_col.update_one(
        {"user_id": user_id},
        {"$set": data}
    )
    return result.modified_count


def deleteUser(user_id: str):
    result = users_col.delete_one({"user_id": user_id})
    return result.deleted_count


# ---------------- Local Login ----------------

def authenticateUser(username: str, password: str):
    user = users_col.find_one({"username": username, "auth_provider": "local"})
    if not user:
        return None

    if not passwordHash.verify_password(password, user["password"]):
        return None

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"]
    }


# ---------------- Google Login ----------------

def authenticateWithGoogle(google_token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        google_id = idinfo["sub"]
        email = idinfo["email"]

        user = users_col.find_one({"google_id": google_id})

        if not user:
            # Auto-register Google user
            user_data = {
                "user_id": str(uuid4()),
                "username": email,
                "password": None,
                "role": "user",
                "auth_provider": "google",
                "google_id": google_id,
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            users_col.insert_one(user_data)
            user = user_data

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }

    except Exception:
        return None


# ---------------- JWT ----------------

def generateUserToken(user_id: str):
    return jwtUtility.create_access_token({"user_id": user_id})


def decodeUserToken(token: str):
    return jwtUtility.decode_access_token(token)

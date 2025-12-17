import os
from pymongo import MongoClient
from datetime import datetime
from uuid import uuid4

# MongoDB connection
db_uri = os.getenv("DB_URL")
client = MongoClient(db_uri)

db = client["job_selector_db"]
collection = db["resumes"]


def getAllPdfs(user_id: str):
    # Fetch all resumes belonging to a specific user
    return list(
        collection.find(
            {"user_id": user_id},
            {"_id": 0}
        )
    )


def getPdfById(resume_id: str, user_id: str):
    # Fetch a single resume by resume_id and user ownership
    return collection.find_one(
        {"resume_id": resume_id, "user_id": user_id},
        {"_id": 0}
    )


def getPdfByRole(role: str, user_id: str):
    # Fetch resumes by job role (case-insensitive) for a user
    return list(
        collection.find(
            {
                "user_id": user_id,
                "job_role": {"$regex": role, "$options": "i"}
            },
            {"_id": 0}
        )
    )


def getPdfByDateSubmitted(date: str, user_id: str):
    """
    date format: YYYY-MM-DD
    Fetch resumes submitted on a specific date for a user
    """
    start = datetime.fromisoformat(date)
    end = start.replace(hour=23, minute=59, second=59)

    return list(
        collection.find(
            {
                "user_id": user_id,
                "created_at": {
                    "$gte": start,
                    "$lte": end
                }
            },
            {"_id": 0}
        )
    )


def addPdf(data: dict, user_id: str):
    # Insert resume with ownership and metadata
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    document = {
        **data,
        "user_id": user_id,                 # ownership
        "resume_id": str(uuid4()),          # public ID
        "created_at": datetime.utcnow(),
        "updated_at": None
    }

    result = collection.insert_one(document)
    return result.inserted_id


def updatePdf(resume_id: str, user_id: str, data: dict):
    # Update resume fields (only if it belongs to the user)
    data["updated_at"] = datetime.utcnow()

    result = collection.update_one(
        {"resume_id": resume_id, "user_id": user_id},
        {"$set": data}
    )

    return result.modified_count


def deletePdf(resume_id: str, user_id: str):
    # Delete resume only if it belongs to the user
    result = collection.delete_one(
        {"resume_id": resume_id, "user_id": user_id}
    )

    return result.deleted_count

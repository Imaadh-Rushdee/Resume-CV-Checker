from datetime import datetime

class User:
    def __init__(self, user_id, username, role="user"):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at
        }

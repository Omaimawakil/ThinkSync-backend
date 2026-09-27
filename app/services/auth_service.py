from app.database import db
from app.auth.security import hash_password, verify_password
import uuid

async def get_user_by_username(username: str):
    return await db.users.find_one({"username": username})

async def create_user(username: str, password: str, role: str, full_name: str = None, department: str = None):
    existing = await get_user_by_username(username)
    if existing:
        return None  # caller turns this into a 409
    user_doc = {
        "user_id": f"USR-{uuid.uuid4().hex[:8]}",
        "username": username,
        "hashed_password": hash_password(password),
        "role": role,
        "full_name": full_name,
        "department": department,
    }
    await db.users.insert_one(user_doc)
    return user_doc

async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user
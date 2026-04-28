import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aura.db")

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is not None:
        return _db

    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        from config.settings import MONGODB_URI, DB_NAME

        if not MONGODB_URI:
            raise ValueError("MONGODB_URI is empty — set it in your .env file.")

        _client = MongoClient(MONGODB_URI, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[DB_NAME]
        logger.info("✅ Connected to MongoDB Atlas — database: %s", DB_NAME)
        _ensure_indexes(_db)
        return _db
    except Exception as exc:
        logger.error("❌ MongoDB connection failed: %s", exc)
        raise

def _ensure_indexes(db) -> None:
    try:
        db.contacts.create_index("name", unique=True)
        db.todos.create_index("done")
        db.alerts.create_index([("type", 1), ("active", 1)])
        db.conversations.create_index("session_id")
        db.faces.create_index("name", unique=True)
        db.cache.create_index("key", unique=True)
        db.cache.create_index("expires_at", expireAfterSeconds=0)
        logger.debug("MongoDB indexes ensured.")
    except Exception as exc:
        logger.warning("Could not create indexes: %s", exc)

def get_contact(name: str) -> Optional[Dict]:
    db = get_db()
    return db.contacts.find_one({"name": name.lower()}, {"_id": 0})

def get_all_contacts() -> Dict[str, str]:
    db = get_db()
    docs = list(db.contacts.find({}, {"_id": 0, "name": 1, "phone": 1}))
    return {d["name"]: d["phone"] for d in docs}

def save_contact(name: str, phone: str) -> None:
    db = get_db()
    db.contacts.update_one(
        {"name": name.lower()},
        {"$set": {"name": name.lower(), "phone": phone, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    logger.info("Contact saved: %s", name)

def delete_contact(name: str) -> bool:
    db = get_db()
    result = db.contacts.delete_one({"name": name.lower()})
    return result.deleted_count > 0

def get_todos(pending_only: bool = False) -> List[Dict]:
    db = get_db()
    query = {"done": False} if pending_only else {}
    return list(db.todos.find(query, {"_id": 0}).sort("added", 1))

def add_todo(task: str) -> None:
    db = get_db()
    db.todos.insert_one({
        "task": task,
        "done": False,
        "added": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

def complete_todo(task_fragment: str) -> bool:
    db = get_db()
    doc = db.todos.find_one({"task": {"$regex": task_fragment, "$options": "i"}, "done": False})
    if doc:
        db.todos.update_one({"_id": doc["_id"]}, {"$set": {"done": True, "updated_at": datetime.now(timezone.utc)}})
        return True
    return False

def clear_todos() -> None:
    db = get_db()
    db.todos.delete_many({})

def get_alerts(alert_type: Optional[str] = None, active_only: bool = True) -> List[Dict]:
    db = get_db()
    query: Dict[str, Any] = {}
    if alert_type:
        query["type"] = alert_type
    if active_only:
        query["active"] = True
    return list(db.alerts.find(query, {"_id": 0}))

def add_alert(alert_type: str, data: Dict) -> None:
    db = get_db()
    db.alerts.insert_one({
        "type": alert_type,
        "data": data,
        "active": True,
        "created_at": datetime.now(timezone.utc),
    })

def deactivate_alert(alert_type: str, data_query: Dict) -> None:
    db = get_db()
    db.alerts.update_many({"type": alert_type, **data_query}, {"$set": {"active": False}})

def save_conversation(session_id: str, messages: List[Dict]) -> None:
    db = get_db()
    db.conversations.update_one(
        {"session_id": session_id},
        {"$set": {"messages": messages, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

def load_conversation(session_id: str) -> List[Dict]:
    db = get_db()
    doc = db.conversations.find_one({"session_id": session_id}, {"_id": 0, "messages": 1})
    return doc["messages"] if doc else []

def get_recent_conversations(limit: int = 10) -> List[Dict]:
    db = get_db()
    return list(
        db.conversations.find({}, {"_id": 0, "session_id": 1, "updated_at": 1})
        .sort("updated_at", -1)
        .limit(limit)
    )

def save_face(name: str, encoding_bytes: bytes) -> None:
    db = get_db()
    from bson.binary import Binary
    db.faces.update_one(
        {"name": name.lower()},
        {"$set": {"name": name.lower(), "encoding": Binary(encoding_bytes), "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

def get_all_faces() -> List[Dict]:
    db = get_db()
    docs = list(db.faces.find({}, {"_id": 0}))
    return [{"name": d["name"], "encoding": bytes(d["encoding"])} for d in docs]

def cache_set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    from datetime import timedelta
    db = get_db()
    expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    db.cache.update_one(
        {"key": key},
        {"$set": {"key": key, "value": value, "expires_at": expires}},
        upsert=True,
    )

def cache_get(key: str) -> Optional[Any]:
    db = get_db()
    doc = db.cache.find_one({"key": key, "expires_at": {"$gt": datetime.now(timezone.utc)}})
    return doc["value"] if doc else None

def ping() -> bool:
    try:
        get_db()
        return True
    except Exception:
        return False

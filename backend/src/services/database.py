"""MongoDB database connection and configuration."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from src.config import settings

# Global database client and database instances
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo():
    """Create database connection."""
    global _client, _database
    # Add connection timeout and server selection timeout
    # Write concern is set at the collection level, not client level
    _client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=5000,  # 5 seconds timeout for server selection
        connectTimeoutMS=10000,  # 10 seconds timeout for connection
        socketTimeoutMS=30000,  # 30 seconds timeout for socket operations
    )
    _database = _client[settings.mongodb_database]

    # Motor defaults to acknowledged writes (w=1), so we don't need to set write_concern explicitly
    # All async operations in Motor automatically wait for write acknowledgment

    # Verify connection
    await _client.admin.command("ping")
    return _database


async def close_mongo_connection():
    """Close database connection."""
    global _client
    if _client:
        _client.close()


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _database


async def create_indexes():
    """Create database indexes."""
    db = get_database()

    # User collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("created_at")

    # Session collection indexes
    await db.sessions.create_index("token", unique=True)
    await db.sessions.create_index("user_id")
    await db.sessions.create_index("expires_at")
    await db.sessions.create_index([("user_id", 1), ("expires_at", 1)])

    # Application collection indexes
    await db.applications.create_index("user_id")
    await db.applications.create_index([("user_id", 1), ("created_at", -1)])
    await db.applications.create_index("status")
    await db.applications.create_index("container_id")
    await db.applications.create_index("created_at")

    # Conversation collection indexes
    await db.conversations.create_index("application_id")
    await db.conversations.create_index("user_id")
    await db.conversations.create_index([("application_id", 1), ("created_at", -1)])
    await db.conversations.create_index("created_at")

    # Container collection indexes
    await db.containers.create_index("container_id", unique=True)
    await db.containers.create_index("application_id")
    await db.containers.create_index("status")
    await db.containers.create_index("created_at")


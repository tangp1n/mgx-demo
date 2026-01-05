"""Conversation service for managing dialogues between user and system."""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...models.conversation import (
    Conversation,
    ConversationCreate,
    Message,
    MessageRole,
    ConversationStatus
)


class ConversationService:
    """Service for managing conversations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize conversation service with database connection."""
        self.db = db
        self.collection = db.conversations

    async def create(
        self,
        user_id: str,
        data: ConversationCreate
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID who is creating the conversation
            data: Conversation creation data

        Returns:
            Created conversation
        """
        conversation = Conversation(
            application_id=data.application_id,
            user_id=user_id,
            messages=[],
            status=ConversationStatus.ACTIVE
        )

        result = await self.collection.insert_one(
            conversation.dict(by_alias=True, exclude={"id"})
        )
        conversation.id = str(result.inserted_id)

        return conversation

    async def get(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID to filter by (for authorization)

        Returns:
            Conversation if found, None otherwise
        """
        query = {"_id": ObjectId(conversation_id)}
        if user_id:
            query["user_id"] = user_id

        doc = await self.collection.find_one(query)
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        return Conversation(**doc)

    async def get_by_application(
        self,
        application_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Get the conversation for an application.

        Args:
            application_id: Application ID
            user_id: Optional user ID to filter by (for authorization)

        Returns:
            Conversation if found, None otherwise
        """
        query = {"application_id": application_id}
        if user_id:
            query["user_id"] = user_id

        doc = await self.collection.find_one(query)
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        return Conversation(**doc)

    async def add_message(
        self,
        conversation_id: str,
        message: Message,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            message: Message to add
            user_id: Optional user ID (for authorization)

        Returns:
            Updated conversation if found, None otherwise
        """
        query = {"_id": ObjectId(conversation_id)}
        if user_id:
            query["user_id"] = user_id

        result = await self.collection.find_one_and_update(
            query,
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Conversation(**result)

    async def add_message_by_application(
        self,
        application_id: str,
        message: Message,
        user_id: str
    ) -> Optional[Conversation]:
        """
        Add a message to a conversation by application ID.

        Args:
            application_id: Application ID
            message: Message to add
            user_id: User ID (for authorization)

        Returns:
            Updated conversation if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"application_id": application_id, "user_id": user_id},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Conversation(**result)

    async def update_status(
        self,
        conversation_id: str,
        status: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Update conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status
            user_id: Optional user ID (for authorization)

        Returns:
            Updated conversation if found, None otherwise
        """
        query = {"_id": ObjectId(conversation_id)}
        if user_id:
            query["user_id"] = user_id

        result = await self.collection.find_one_and_update(
            query,
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Conversation(**result)

    async def delete(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one(
            {"_id": ObjectId(conversation_id), "user_id": user_id}
        )

        return result.deleted_count > 0

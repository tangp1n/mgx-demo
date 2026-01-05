"""Conversations API endpoints with SSE streaming."""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.conversation import (
    ConversationResponse,
    MessageCreate,
    Message,
    MessageRole
)
from ..services.conversation import ConversationService
from ..services.application import ApplicationService
from ..services.database import get_database
from ..middleware.auth import get_current_user
from ..agents.app_creator import AppCreatorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["conversations"])


async def get_conv_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(db)


async def get_app_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ApplicationService:
    """Get application service instance."""
    return ApplicationService(db)


@router.post("/{application_id}/conversation", status_code=status.HTTP_202_ACCEPTED)
async def send_message(
    application_id: str,
    data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conv_service),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Send a message to the conversation and trigger agent processing.

    Args:
        application_id: Application ID
        data: Message data
        current_user: Current authenticated user
        conv_service: Conversation service
        app_service: Application service

    Returns:
        Stream URL for receiving agent responses

    Raises:
        HTTPException: If application or conversation not found
    """
    # Verify application exists and belongs to user
    app = await app_service.get(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Get or create conversation
    conversation = await conv_service.get_by_application(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Add user message to conversation
    user_message = Message(
        role=MessageRole.USER,
        content=data.content
    )

    await conv_service.add_message(
        conversation_id=conversation.id,
        message=user_message,
        user_id=current_user["user_id"]
    )

    # Return stream URL
    return {
        "stream_url": f"/api/v1/applications/{application_id}/conversation/stream",
        "message": "Message received. Connect to stream_url for agent responses."
    }


@router.get("/{application_id}/conversation/stream")
async def stream_conversation(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conv_service),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Stream conversation events via SSE.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        conv_service: Conversation service
        app_service: Application service

    Returns:
        SSE stream of conversation events

    Raises:
        HTTPException: If application or conversation not found
    """
    # Verify application exists and belongs to user
    app = await app_service.get(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Get conversation
    conversation = await conv_service.get_by_application(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get last user message
    messages = conversation.messages
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No messages in conversation"
        )

    # Get last user message
    last_user_message = None
    for msg in reversed(messages):
        if msg.role == MessageRole.USER:
            last_user_message = msg
            break

    if not last_user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found"
        )

    # Convert messages to LangChain format for agent
    from langchain_core.messages import HumanMessage, AIMessage

    lc_messages = []
    for msg in messages[:-1]:  # Exclude the last message as it will be passed separately
        if msg.role == MessageRole.USER:
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == MessageRole.ASSISTANT:
            lc_messages.append(AIMessage(content=msg.content))

    # Create agent and stream response
    agent = AppCreatorAgent()

    async def save_assistant_message(content: str):
        """Background task to save assistant message."""
        if not content:
            return
        try:
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=content
            )
            await conv_service.add_message_by_application(
                application_id=application_id,
                message=assistant_message,
                user_id=current_user["user_id"]
            )
            logger.info(f"Saved assistant message for application {application_id}")
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}", exc_info=True)

    async def event_generator():
        """Generate SSE events from agent and save assistant message when done."""
        assistant_content = ""
        seen_text_contents = set()  # Track seen text content to avoid duplicates
        requirements_confirmed = False
        confirmed_requirements = None

        # Pre-fetch application to avoid blocking in the middle of the stream
        app = None
        try:
            app = await asyncio.wait_for(
                app_service.get(
                    application_id=application_id,
                    user_id=current_user["user_id"]
                ),
                timeout=5.0  # 5 second timeout
            )
            logger.info(f"Pre-fetched application: {'found' if app else 'not found'}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching application {application_id}")
        except Exception as e:
            logger.error(f"Failed to pre-fetch application {application_id}: {e}", exc_info=True)

        try:
            async for event in agent.stream_conversation(
                application_id=application_id,
                user_id=current_user["user_id"],
                user_message=last_user_message.content,
                existing_messages=lc_messages,
                app_service=app_service
            ):
                # Yield control to event loop to prevent blocking in nested async generators
                await asyncio.sleep(0)

                # Extract text content from events
                if event.startswith("data: "):
                    try:
                        event_data = json.loads(event[6:])  # Remove "data: " prefix
                        event_type = event_data.get("type")

                        # Check for requirements_confirmed event
                        if event_type == "requirements_confirmed":
                            requirements_confirmed = True
                            confirmed_requirements = event_data.get("data", {}).get("requirements", "")
                            logger.info("🎯 Requirements confirmed event received from agent")

                        if event_type == "text":
                            # Accumulate text content (keep the longest/latest complete content)
                            content = event_data.get("data", {}).get("content", "")
                            if content:
                                # Use content as hash to track duplicates
                                content_hash = content

                                # Only update if we haven't seen this exact content before
                                # or if the new content is longer (might be a more complete version)
                                if content_hash not in seen_text_contents:
                                    seen_text_contents.add(content_hash)
                                    assistant_content = content
                                    logger.info(f"Updated assistant_content (length: {len(content)})")
                                elif len(content) > len(assistant_content):
                                    # If same content but longer, update (shouldn't happen, but safety)
                                    assistant_content = content
                                    logger.info(f"Updated assistant_content with longer version (length: {len(content)})")
                                else:
                                    logger.debug(f"Skipping duplicate text content (length: {len(content)})")
                    except (json.JSONDecodeError, KeyError):
                        pass

                yield event

                # Check if stream is done
                if event.strip() == "data: [DONE]":
                    # Create background task to save message
                    if assistant_content:
                        logger.info(f"Saving assistant message (length: {len(assistant_content)})")
                        asyncio.create_task(save_assistant_message(assistant_content))
                    else:
                        logger.warning("No assistant content to save")

                    # Note: Code generation is now triggered manually by the user via the frontend button
                    # The requirements_confirmed event is still emitted so the frontend can show the button
                    if requirements_confirmed:
                        logger.info("🎯 Requirements confirmed - waiting for user to manually trigger code generation")

                    break
        except Exception as e:
            logger.error(f"Error in event generator: {e}", exc_info=True)
            yield f'data: {{"type": "error", "data": {{"message": "Internal server error"}}, "timestamp": ""}}\n\n'
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{application_id}/conversation", response_model=ConversationResponse)
async def get_conversation(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conv_service),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Get conversation for an application.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        conv_service: Conversation service
        app_service: Application service

    Returns:
        Conversation

    Raises:
        HTTPException: If application or conversation not found
    """
    # Verify application exists and belongs to user
    app = await app_service.get(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Get conversation
    conversation = await conv_service.get_by_application(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return ConversationResponse(**conversation.dict(by_alias=True))

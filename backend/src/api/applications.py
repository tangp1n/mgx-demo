"""Applications API endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate
)
from ..models.conversation import ConversationCreate
from ..services.application import ApplicationService
from ..services.conversation import ConversationService
from ..services.container.container_lifecycle import ContainerLifecycleService
from ..services.database import get_database
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


async def get_app_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ApplicationService:
    """Get application service instance."""
    return ApplicationService(db)


async def get_conv_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(db)


async def get_container_lifecycle(db: AsyncIOMotorDatabase = Depends(get_database)) -> ContainerLifecycleService:
    """Get container lifecycle service instance."""
    return ContainerLifecycleService(db)


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service),
    conv_service: ConversationService = Depends(get_conv_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new application.

    Args:
        data: Application creation data
        current_user: Current authenticated user
        app_service: Application service
        conv_service: Conversation service
        db: Database connection

    Returns:
        Created application
    """
    # Create application
    app = await app_service.create(
        user_id=current_user["user_id"],
        data=data
    )

    # Create initial conversation for the application
    await conv_service.create(
        user_id=current_user["user_id"],
        data=ConversationCreate(application_id=app.id)
    )

    # Create container for the application
    try:
        from ..services.container.container_lifecycle import ContainerLifecycleService
        from ..models.container import ResourceLimits

        container_lifecycle = ContainerLifecycleService(db)
        resource_limits = ResourceLimits(memory_mb=512, cpu_cores=0.5)

        container = await container_lifecycle.create_and_start_container(
            application_id=app.id,
            image="node:18-alpine",
            resource_limits=resource_limits
        )

        # Update application with container ID
        await app_service.update_container(
            application_id=app.id,
            container_id=container.container_id
        )

        logger.info(f"Created container {container.container_id[:12]} for application {app.id}")
    except Exception as e:
        logger.error(f"Failed to create container for application {app.id}: {e}", exc_info=True)
        # Don't fail the application creation if container creation fails
        # The container can be created later during code generation

    return ApplicationResponse(**app.dict(by_alias=True))


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Get an application by ID.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        app_service: Application service

    Returns:
        Application

    Raises:
        HTTPException: If application not found
    """
    app = await app_service.get(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    return ApplicationResponse(**app.dict(by_alias=True))


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    List applications for the current user.

    Args:
        skip: Number of applications to skip (pagination)
        limit: Maximum number of applications to return
        current_user: Current authenticated user
        app_service: Application service

    Returns:
        List of applications
    """
    apps = await app_service.list(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit
    )

    return [ApplicationResponse(**app.dict(by_alias=True)) for app in apps]


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: str,
    data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Update an application.

    Args:
        application_id: Application ID
        data: Application update data
        current_user: Current authenticated user
        app_service: Application service

    Returns:
        Updated application

    Raises:
        HTTPException: If application not found
    """
    app = await app_service.update(
        application_id=application_id,
        user_id=current_user["user_id"],
        data=data
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    return ApplicationResponse(**app.dict(by_alias=True))


@router.post("/{application_id}/confirm-requirements", response_model=ApplicationResponse, deprecated=True)
async def confirm_requirements(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Confirm application requirements and trigger code generation.

    **DEPRECATED**: This endpoint is deprecated. Requirements are now automatically
    confirmed during the conversation flow. Code generation is triggered automatically
    after confirmation. This endpoint is kept for backward compatibility only.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        app_service: Application service

    Returns:
        Updated application with generation stream URL

    Raises:
        HTTPException: If application not found
    """
    app = await app_service.confirm_requirements(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Return application with stream URL for code generation progress
    response = ApplicationResponse(**app.dict(by_alias=True))

    return response


@router.get("/{application_id}/generate/stream")
async def stream_code_generation(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Stream code generation progress via SSE.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        app_service: Application service
        db: Database connection

    Returns:
        SSE stream of code generation events

    Raises:
        HTTPException: If application not found or not ready for generation
    """
    from ..services.agent.code_gen_service import CodeGenService
    from ..utils.sse_formatter import SSEFormatter

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

    if not app.requirements_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirements must be confirmed before code generation"
        )

    # Create code generation service
    code_gen_service = CodeGenService(db)
    sse_formatter = SSEFormatter()

    async def event_generator():
        """Generate SSE events from code generation."""
        try:
            async for event in code_gen_service.generate_and_deploy(
                application_id=app.id,
                requirements=app.requirements
            ):
                # Format as SSE event
                sse_event = sse_formatter.format_event(event)
                yield sse_event

            # Send done signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Code generation failed: {e}", exc_info=True)
            error_event = sse_formatter.format_event({
                "type": "error",
                "data": {
                    "message": f"Code generation failed: {str(e)}",
                    "error": str(e)
                }
            })
            yield error_event
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


@router.get("/{application_id}/preview")
async def get_preview(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Get preview information for an application.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        app_service: Application service

    Returns:
        Preview information (URL, port, status)

    Raises:
        HTTPException: If application not found
    """
    app = await app_service.get(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    return {
        "preview_url": app.preview_url,
        "port": app.port,
        "status": app.status,
        "container_id": app.container_id
    }


@router.get("/{application_id}/files")
async def get_file_tree(
    application_id: str,
    path: str = "/app",
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service),
    container_lifecycle: ContainerLifecycleService = Depends(get_container_lifecycle)
):
    """
    Get file tree for an application.

    Args:
        application_id: Application ID
        path: Root path (default: /app)
        current_user: Current authenticated user
        app_service: Application service
        container_lifecycle: Container lifecycle service

    Returns:
        File tree structure

    Raises:
        HTTPException: If application or container not found
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

    try:
        file_tree = await container_lifecycle.get_file_tree(application_id, path)
        return {"files": file_tree}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file tree: {str(e)}"
        )


@router.get("/{application_id}/files/{file_path:path}")
async def get_file_content(
    application_id: str,
    file_path: str,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service),
    container_lifecycle: ContainerLifecycleService = Depends(get_container_lifecycle)
):
    """
    Get file content from an application.

    Args:
        application_id: Application ID
        file_path: File path in container
        current_user: Current authenticated user
        app_service: Application service
        container_lifecycle: Container lifecycle service

    Returns:
        File content

    Raises:
        HTTPException: If application, container, or file not found
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

    try:
        content = await container_lifecycle.get_file_content(
            application_id,
            f"/{file_path}" if not file_path.startswith('/') else file_path
        )

        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        return {"content": content, "path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file content: {str(e)}"
        )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    app_service: ApplicationService = Depends(get_app_service)
):
    """
    Delete an application.

    Args:
        application_id: Application ID
        current_user: Current authenticated user
        app_service: Application service

    Raises:
        HTTPException: If application not found
    """
    deleted = await app_service.delete(
        application_id=application_id,
        user_id=current_user["user_id"]
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

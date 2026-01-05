#!/usr/bin/env python3
"""Diagnostic script to check container status and file tree."""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from src.services.container.container_service import ContainerService
from src.services.container.container_lifecycle import ContainerLifecycleService
from src.services.application.application_service import ApplicationService
from src.containers.docker_client import DockerClient

async def check_application(application_id: str):
    """Check application, container, and file tree status."""
    # Connect to MongoDB
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "appbuilder")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    try:
        # Check application
        app_service = ApplicationService(db)
        # Get application without user check for diagnostic
        app = await app_service.get(application_id, user_id=None)

        if not app:
            print(f"❌ Application {application_id} not found")
            return

        print(f"✅ Application found: {app.name or 'Unnamed'}")
        print(f"   Status: {app.status}")
        print(f"   Container ID: {app.container_id or 'None'}")
        print(f"   Requirements confirmed: {app.requirements_confirmed}")
        print(f"   Requirements: {app.requirements[:100] if app.requirements else 'None'}...")
        print()

        # Check container
        container_service = ContainerService(db)
        container = await container_service.get_by_application(application_id)

        if not container:
            print("❌ No container found for this application")
            print("   This might mean code generation hasn't started yet or container creation failed")
            return

        print(f"✅ Container found: {container.container_id[:12]}")
        print(f"   Status: {container.status}")
        print()

        # Check Docker container status
        docker = DockerClient()
        try:
            docker_container = docker.client.containers.get(container.container_id)
            print(f"✅ Docker container exists")
            print(f"   Docker status: {docker_container.status}")
            print(f"   Image: {docker_container.image.tags[0] if docker_container.image.tags else 'Unknown'}")
            print()
        except Exception as e:
            print(f"❌ Docker container not found or error: {e}")
            print()
            return

        # Check file tree
        container_lifecycle = ContainerLifecycleService(db)
        try:
            file_tree = await container_lifecycle.get_file_tree(application_id, "/app")

            if not file_tree:
                print("⚠️  File tree is empty - no files found in /app directory")
                print("   This could mean:")
                print("   - Code generation is still in progress")
                print("   - Code generation hasn't started yet")
                print("   - Code generation failed silently")
            else:
                print(f"✅ File tree found with {len(file_tree)} items:")
                def print_tree(items, indent=0):
                    for item in items:
                        prefix = "  " * indent
                        icon = "📁" if item["type"] == "directory" else "📄"
                        print(f"{prefix}{icon} {item['name']} ({item['type']})")
                        if item.get("children"):
                            print_tree(item["children"], indent + 1)

                print_tree(file_tree)
        except Exception as e:
            print(f"❌ Error getting file tree: {e}")
            import traceback
            traceback.print_exc()

    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_container_status.py <application_id>")
        sys.exit(1)

    application_id = sys.argv[1]
    asyncio.run(check_application(application_id))


# Data Model: AI-Powered Conversational App Builder Platform

**Date**: 2026-01-04
**Feature**: 001-ai-app-builder

This document defines the data entities, their attributes, relationships, and validation rules for the platform.

## Entities

### User

Represents a user account in the system.

**Attributes**:
- `_id` (ObjectId): Primary key
- `email` (string, required, unique): User email address
- `password_hash` (string, required): Hashed password (never return to client)
- `created_at` (datetime, required): Account creation timestamp
- `updated_at` (datetime, required): Last update timestamp

**Validation Rules**:
- Email must be valid format
- Password must meet security requirements (min length, complexity)
- Email must be unique across all users

**Relationships**:
- One-to-many with Session
- One-to-many with Application
- One-to-many with Conversation

**State Transitions**: N/A (stateless entity)

### Session

Represents an active user session for authentication.

**Attributes**:
- `_id` (ObjectId): Primary key
- `user_id` (ObjectId, required, indexed): Reference to User
- `token` (string, required, unique, indexed): Session token
- `expires_at` (datetime, required, indexed): Session expiration timestamp
- `created_at` (datetime, required): Session creation timestamp
- `ip_address` (string, optional): Client IP address for security
- `user_agent` (string, optional): Client user agent

**Validation Rules**:
- Token must be unique
- Expires_at must be in the future when created
- User_id must reference existing user

**Relationships**:
- Many-to-one with User

**State Transitions**:
- Created → Active → Expired (automatic based on expires_at)
- Can be revoked (deleted) at any time

### Application

Represents a user-created application with its requirements, generated code, and runtime state.

**Attributes**:
- `_id` (ObjectId): Primary key
- `user_id` (ObjectId, required, indexed): Reference to User
- `name` (string, optional): User-provided application name
- `requirements` (string, required): User requirements description
- `requirements_confirmed` (boolean, default: false): Whether user confirmed requirements
- `status` (enum, required, indexed): Application status
  - Values: `draft`, `requirements_confirmed`, `generating`, `deploying`, `running`, `stopped`, `error`
- `container_id` (string, optional, indexed): Docker container identifier
- `preview_url` (string, optional): URL to access running application preview
- `port` (integer, optional): Port number for preview access
- `created_at` (datetime, required, indexed): Creation timestamp
- `updated_at` (datetime, required): Last update timestamp
- `last_deployed_at` (datetime, optional): Last deployment timestamp

**Validation Rules**:
- Requirements cannot be empty
- Status transitions must be valid (see state transitions)
- Container_id must be valid Docker container ID format when set
- Preview_url must be valid URL format when set
- Port must be in valid port range (1024-65535) when set
- User_id must reference existing user

**Relationships**:
- Many-to-one with User
- One-to-many with Conversation
- One-to-one with Container (via container_id)

**State Transitions**:
- `draft` → `requirements_confirmed` (when user confirms requirements)
- `requirements_confirmed` → `generating` (when code generation starts)
- `generating` → `deploying` (when code generation completes)
- `deploying` → `running` (when container starts successfully)
- `deploying` → `error` (when deployment fails)
- `running` → `stopped` (when container stops)
- `running` → `error` (when container crashes)
- `stopped` → `running` (when restarted)
- `error` → `generating` (when regenerating after error)

### Conversation

Represents the dialogue between user and system for a specific application.

**Attributes**:
- `_id` (ObjectId): Primary key
- `application_id` (ObjectId, required, indexed): Reference to Application
- `user_id` (ObjectId, required, indexed): Reference to User
- `messages` (array of Message objects, required): Conversation messages
  - Message object:
    - `role` (enum, required): `user` or `assistant`
    - `content` (string, required): Message content
    - `timestamp` (datetime, required): Message timestamp
    - `events` (array of Event objects, optional): Agent events (for assistant messages)
      - Event object:
        - `type` (enum, required): `thought`, `tool_call`, `tool_call_result`, `text`, `error`
        - `data` (object, required): Event-specific data
        - `timestamp` (datetime, required): Event timestamp
- `status` (enum, required): Conversation status
  - Values: `active`, `paused`, `completed`, `error`
- `created_at` (datetime, required, indexed): Creation timestamp
- `updated_at` (datetime, required): Last update timestamp

**Validation Rules**:
- Application_id must reference existing application
- User_id must reference existing user
- Messages array cannot be empty
- Message roles must be valid enum values
- Event types must be valid enum values
- Messages must be in chronological order (by timestamp)

**Relationships**:
- Many-to-one with Application
- Many-to-one with User

**State Transitions**:
- `active` → `paused` (when conversation is paused)
- `active` → `completed` (when conversation completes)
- `active` → `error` (when error occurs)
- `paused` → `active` (when conversation resumes)
- `error` → `active` (when error is resolved)

### Container

Represents an isolated runtime environment for executing user applications.

**Attributes**:
- `_id` (ObjectId): Primary key
- `application_id` (ObjectId, required, indexed): Reference to Application
- `container_id` (string, required, unique, indexed): Docker container identifier
- `image` (string, required): Docker base image (e.g., "node:18", "python:3.11")
- `status` (enum, required, indexed): Container status
  - Values: `creating`, `running`, `stopped`, `error`
- `port` (integer, optional): Exposed port for application access
- `resource_limits` (object, optional): Resource constraints
  - `memory_mb` (integer): Memory limit in MB
  - `cpu_cores` (float): CPU limit in cores
- `created_at` (datetime, required, indexed): Creation timestamp
- `updated_at` (datetime, required): Last update timestamp
- `stopped_at` (datetime, optional): Stop timestamp

**Validation Rules**:
- Container_id must be valid Docker container ID format
- Image must be valid Docker image reference
- Status transitions must be valid (see state transitions)
- Port must be in valid port range (1024-65535) when set
- Memory_mb must be positive when set
- Cpu_cores must be positive when set
- Application_id must reference existing application

**Relationships**:
- One-to-one with Application (via container_id)

**State Transitions**:
- `creating` → `running` (when container starts successfully)
- `creating` → `error` (when container creation fails)
- `running` → `stopped` (when container stops)
- `running` → `error` (when container crashes)
- `stopped` → `running` (when container restarts)
- `error` → `creating` (when recreating after error)

## Database Indexes

### User Collection
- `email` (unique index)
- `created_at` (index for sorting)

### Session Collection
- `token` (unique index)
- `user_id` (index)
- `expires_at` (TTL index for auto-cleanup)
- `user_id + expires_at` (compound index for active session queries)

### Application Collection
- `user_id` (index)
- `user_id + created_at` (compound index for user's applications list)
- `status` (index)
- `container_id` (index)
- `created_at` (index for sorting)

### Conversation Collection
- `application_id` (index)
- `user_id` (index)
- `application_id + created_at` (compound index for conversation history)
- `created_at` (index for sorting)

### Container Collection
- `container_id` (unique index)
- `application_id` (index)
- `status` (index)
- `created_at` (index for sorting)

## Data Constraints and Business Rules

1. **User-Application Relationship**: Users can create multiple applications. Applications belong to exactly one user.

2. **Application-Conversation Relationship**: Each application has one active conversation at a time. Conversations can be paused and resumed.

3. **Application-Container Relationship**: Each application has at most one container at a time. Container lifecycle is managed independently but linked to application status.

4. **Container Cleanup**: Containers should be cleaned up (stopped and removed) when:
   - Application is deleted
   - Container status is `error` for extended period
   - Container is `stopped` and application is not `running`

5. **Session Expiration**: Sessions expire after configured time period (e.g., 24 hours). Expired sessions should be cleaned up automatically.

6. **Conversation Message Limits**: To prevent unbounded growth, conversations should have a maximum message count (e.g., 1000 messages). Older messages can be archived.

7. **Application Status Consistency**: Application status should reflect container status:
   - Application `running` requires container `running`
   - Application `error` if container `error`
   - Application `stopped` if container `stopped`


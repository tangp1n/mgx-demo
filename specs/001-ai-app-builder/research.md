# Research: AI-Powered Conversational App Builder Platform

**Date**: 2026-01-04
**Feature**: 001-ai-app-builder

This document consolidates research findings and technical decisions for implementing the AI-powered conversational app builder platform.

## 1. LangGraph Multi-Agent Architecture

### Decision: Hierarchical Agent Structure with Main Agent and Code Generation Sub-Agent

**Rationale**:
- The system requires separation of concerns: conversation management (requirements gathering) vs. code generation/execution
- LangGraph supports state machines and sub-graphs, allowing one agent to invoke another as a tool
- This pattern enables independent testing, optimization, and maintenance of each agent

**Implementation Pattern**:
- **Main Agent (app_creator)**: Handles conversation with user, requirement clarification, confirmation. Uses LangGraph StateGraph with nodes for conversation, requirement extraction, confirmation
- **Code Generation Sub-Agent (code_gen)**: Invoked by main agent after requirements are confirmed. Manages file operations, command execution, dependency installation, dev server startup. Uses LangGraph with tool-calling nodes
- **Communication**: Main agent invokes code_gen sub-agent as a tool/function. Code_gen returns status and results to main agent

**Alternatives Considered**:
- **Single monolithic agent**: Rejected because mixing conversation logic with code generation makes both harder to maintain, test, and optimize
- **Separate independent agents**: Rejected because coordination and state sharing becomes complex without a clear hierarchy

**Key LangGraph Features to Use**:
- StateGraph for agent state management
- Sub-graphs for sub-agent invocation
- Streaming support for real-time updates
- Tool integration for file/command operations

## 2. ag-ui Protocol for SSE Streaming

### Decision: Implement ag-ui Protocol for Agent Event Streaming

**Rationale**:
- ag-ui protocol provides standardized event types for agent communication
- CopilotKit frontend expects ag-ui protocol events
- Ensures compatibility and future extensibility

**Event Types**:
- `thought`: Agent thinking/reasoning steps
- `tool_call`: Agent invoking a tool (with tool name, arguments)
- `tool_call_result`: Tool execution result (success/failure, output)
- `text`: Text responses to user
- `error`: Error events

**Implementation**:
- Backend: Format agent outputs (from LangGraph streams) into ag-ui protocol events
- Frontend: CopilotKit consumes these events and renders appropriately
- SSE format: `data: {json_event}\n\n` with event type and payload

**Alternatives Considered**:
- **Custom protocol**: Rejected because CopilotKit requires ag-ui protocol, and standardization is valuable
- **WebSocket**: Rejected because SSE is simpler for one-way streaming (server→client), and ag-ui/CopilotKit are designed for SSE

## 3. CopilotKit React Integration

### Decision: Use CopilotKit Components for Conversation UI

**Rationale**:
- CopilotKit provides ready-made components for AI conversation interfaces
- Handles ag-ui protocol event parsing and rendering
- Provides good UX patterns (message bubbles, streaming indicators, tool call visualization)
- Reduces frontend development effort while maintaining quality

**Key Components**:
- `CopilotKit` provider wrapper
- `CopilotSidebar` or `CopilotPopup` for conversation interface
- SSE integration for streaming events
- Built-in support for tool call visualization

**Integration Pattern**:
- Wrap main app with CopilotKit provider
- Configure SSE endpoint URL
- CopilotKit handles event parsing and UI rendering
- Custom components can be added for code preview and app preview areas

**Alternatives Considered**:
- **Custom conversation UI**: Rejected because CopilotKit provides proven patterns and reduces development time significantly
- **Other conversation UI libraries**: Rejected because CopilotKit has best ag-ui protocol support

## 4. FastAPI SSE Implementation

### Decision: Use FastAPI StreamingResponse with SSE Format

**Rationale**:
- FastAPI's StreamingResponse supports SSE natively
- Async generators allow streaming LangGraph agent outputs
- Standard SSE format ensures browser compatibility

**Implementation Pattern**:
```python
from fastapi.responses import StreamingResponse
import json

async def stream_agent_events(session_id: str):
    async for event in agent_stream(session_id):
        # Format as ag-ui protocol event
        formatted = format_agui_event(event)
        yield f"data: {json.dumps(formatted)}\n\n"

    yield "data: [DONE]\n\n"

@router.get("/conversations/{session_id}/stream")
async def stream_conversation(session_id: str):
    return StreamingResponse(
        stream_agent_events(session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

**Key Considerations**:
- Keep-alive connections to prevent timeout
- Proper error handling and connection cleanup
- Event formatting according to ag-ui protocol
- Graceful handling of client disconnections

**Alternatives Considered**:
- **WebSocket**: Rejected because SSE is simpler for server→client streaming, and frontend (CopilotKit) expects SSE
- **Polling**: Rejected because real-time requirements demand streaming, and polling creates latency

## 5. Docker SDK for Container Communication

### Decision: Use Docker SDK (docker-py) for Container Management and Communication

**Rationale**:
- Docker SDK provides Python-native interface to Docker daemon
- Supports container creation, execution, file operations, networking
- Required for security isolation of user-generated code

**Key Operations**:
- **Container Creation**: Create containers with base images (e.g., node:18, python:3.11)
- **File Operations**: Copy files into containers, read files from containers
- **Command Execution**: Execute commands in running containers (e.g., `npm install`, `npm start`)
- **Network Management**: Expose ports, create networks for application access
- **Lifecycle Management**: Start, stop, remove containers

**Implementation Pattern**:
```python
import docker

client = docker.from_env()

# Create container
container = client.containers.create(
    image="node:18",
    command="tail -f /dev/null",  # Keep container running
    detach=True
)

# Execute command
exec_result = container.exec_run("npm install", workdir="/app")

# Copy files
container.put_archive("/app", tar_stream)

# Read files
bits, stat = container.get_archive("/app/file.js")
```

**Security Considerations**:
- Resource limits (memory, CPU) per container
- Network isolation
- Read-only filesystem where possible
- Container cleanup after session ends
- No privileged mode

**Alternatives Considered**:
- **Kubernetes**: Rejected because Docker is sufficient for this use case, and K8s adds unnecessary complexity for single-container-per-application pattern
- **Process-based execution**: Rejected because containers provide better isolation and security

## 6. MongoDB Schema Design

### Decision: Document-Based Storage with Embedded Subdocuments

**Rationale**:
- Conversation history is naturally hierarchical (conversation → messages)
- Application data includes flexible metadata (generated files, container info)
- MongoDB's flexible schema suits evolving agent outputs

**Collection Structure**:
- **users**: User accounts (email, password hash, created_at, etc.)
- **sessions**: User sessions (user_id, token, expires_at)
- **conversations**: Conversation threads (user_id, application_id, messages[], status, created_at, updated_at)
- **applications**: Generated applications (user_id, requirements, container_id, preview_url, status, created_at, updated_at)
- **containers**: Container metadata (application_id, container_id, status, resource_limits, created_at)

**Key Design Decisions**:
- Embed messages in conversations collection (avoid joins, fast retrieval)
- Separate applications and containers collections (container lifecycle independent)
- Index on user_id, session_id, container_id for fast lookups
- TTL indexes for temporary data cleanup

**Alternatives Considered**:
- **SQL database**: Rejected because conversation data is naturally document-based, and MongoDB provides better fit for hierarchical/nested data
- **Flat message storage**: Rejected because embedding messages provides better query performance and simpler data model

## 7. Container Security and Isolation

### Decision: Per-Application Container with Resource Limits and Network Isolation

**Rationale**:
- Security requirement: User-generated code must not access other users' data or system resources
- Isolation requirement: Each application runs in its own container
- Resource limits prevent resource exhaustion

**Security Measures**:
- **Resource Limits**: Memory (e.g., 512MB), CPU (e.g., 0.5 cores) per container
- **Network Isolation**: Containers on isolated Docker networks, only expose necessary ports
- **Filesystem**: Use volume mounts for application code, read-only base image layers
- **User Permissions**: Run containers as non-root user
- **Timeout**: Auto-stop containers after inactivity period
- **Cleanup**: Remove containers after session ends or timeout

**Implementation**:
- Use Docker SDK to set resource limits during container creation
- Create separate Docker networks for isolation
- Implement container lifecycle management (create, start, monitor, stop, remove)
- Log all container operations for audit

**Alternatives Considered**:
- **Shared containers with user namespaces**: Rejected because per-container isolation is simpler and more secure
- **VM-based isolation**: Rejected because containers provide sufficient isolation with better performance and resource efficiency

## 8. LLM Integration and Token Management

### Decision: Built-in LLM API Keys with Configurable Provider Support

**Rationale**:
- User requirement: "LLM token directly built into code"
- Support multiple providers (OpenAI, Anthropic, etc.) for flexibility
- Configuration-based approach allows easy provider switching

**Implementation Pattern**:
- Store API keys in environment variables or config file (not in code repository)
- Use LangChain/LangGraph LLM abstractions for provider-agnostic code
- Support OpenAI, Anthropic Claude, and other LangChain-compatible providers
- Configure per-environment (development, production)

**Configuration Example**:
```python
# config.py
LLM_PROVIDER = "openai"  # or "anthropic"
LLM_API_KEY = os.getenv("OPENAI_API_KEY")  # or ANTHROPIC_API_KEY
LLM_MODEL = "gpt-4"  # or "claude-3-opus"
```

**Alternatives Considered**:
- **User-provided API keys**: Rejected because user requirement specifies built-in keys, and managing user keys adds complexity
- **Single provider only**: Rejected because supporting multiple providers provides flexibility and future-proofing

## Summary

All technical decisions align with the user's requirements and industry best practices. The architecture provides:
- Clear separation of concerns (agents, containers, API, frontend)
- Security through container isolation
- Real-time streaming via SSE and ag-ui protocol
- Scalability through async operations and resource limits
- Maintainability through standard patterns and libraries (LangGraph, CopilotKit, FastAPI)

No unresolved clarifications remain. All technical choices are justified and ready for Phase 1 design.


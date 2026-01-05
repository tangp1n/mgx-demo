# Tasks: AI-Powered Conversational App Builder Platform

**Input**: Design documents from `/specs/001-ai-app-builder/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are not explicitly requested in the specification, so test tasks are not included. Focus is on implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `fe/src/` (from plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend project structure at backend/src/ with directories: models/, services/, api/, agents/, containers/
- [X] T002 Create frontend project structure at fe/src/ with directories: components/, pages/, services/, hooks/, types/, utils/
- [X] T003 Initialize Python backend project with requirements.txt in backend/
- [X] T004 [P] Initialize React frontend project with package.json in fe/
- [X] T005 [P] Create backend/src/config.py for configuration management
- [X] T006 [P] Create backend/src/main.py for FastAPI application entry point
- [X] T007 [P] Create fe/src/App.tsx for React application entry point
- [X] T008 [P] Configure linting and formatting tools (black, flake8 for backend; ESLint, Prettier for frontend)
- [X] T009 [P] Create .env.example files for backend and frontend with required environment variables
- [X] T010 Create README.md with project setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Setup MongoDB connection and async driver (Motor) in backend/src/services/database.py
- [X] T012 [P] Create User model in backend/src/models/user.py with email, password_hash, created_at, updated_at
- [X] T013 [P] Create Session model in backend/src/models/session.py with user_id, token, expires_at, created_at
- [X] T014 Implement authentication service in backend/src/services/auth/auth_service.py (password hashing, verification)
- [X] T015 Implement session service in backend/src/services/session/session_service.py (create, validate, revoke sessions)
- [X] T016 Create authentication middleware in backend/src/middleware/auth.py for bearer token validation
- [X] T017 [P] Implement user registration endpoint in backend/src/api/auth.py (POST /auth/register)
- [X] T018 [P] Implement user login endpoint in backend/src/api/auth.py (POST /auth/login)
- [X] T019 [P] Implement logout endpoint in backend/src/api/auth.py (POST /auth/logout)
- [X] T020 Configure FastAPI app with CORS, error handlers, and middleware in backend/src/main.py
- [X] T021 Create base error handling and response formatting utilities in backend/src/utils/errors.py
- [X] T022 Setup logging infrastructure in backend/src/utils/logger.py
- [X] T023 Create frontend API service client in fe/src/services/api.ts with axios/fetch configuration
- [X] T024 Create TypeScript types for API responses in fe/src/types/api.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Conversational App Requirements Gathering (Priority: P1) 🎯 MVP

**Goal**: Users access the platform and engage in a natural language conversation to describe the application they want to create. The system understands the requirements, asks clarifying questions when needed, and confirms the specifications before generating code.

**Independent Test**: Can be fully tested by having a user describe a simple application (e.g., "a todo list app with add and delete functions") through conversation, and verifying that the system correctly captures and confirms all requirements without generating or running any code.

### Implementation for User Story 1

- [X] T025 [P] [US1] Create Application model in backend/src/models/application.py with user_id, name, requirements, requirements_confirmed, status, created_at, updated_at
- [X] T026 [P] [US1] Create Conversation model in backend/src/models/conversation.py with application_id, user_id, messages array, status, created_at, updated_at
- [X] T027 [US1] Create application service in backend/src/services/application/application_service.py (create, get, update, list applications)
- [X] T028 [US1] Create conversation service in backend/src/services/conversation/conversation_service.py (create, get, add message, update status)
- [X] T029 [US1] Create main app_creator agent in backend/src/agents/app_creator/agent.py using LangGraph with conversation, requirement extraction, and confirmation nodes
- [X] T030 [US1] Implement LLM integration and configuration in backend/src/agents/app_creator/llm_config.py
- [X] T031 [US1] Create agent state management for conversation context in backend/src/agents/app_creator/state.py
- [X] T032 [US1] Implement SSE event formatter for ag-ui protocol in backend/src/utils/sse_formatter.py (thought, tool_call, tool_call_result, text, error events)
- [X] T033 [US1] Implement conversation streaming endpoint (GET /applications/{application_id}/conversation/stream) in backend/src/api/conversations.py with SSE response
- [X] T034 [US1] Implement send message endpoint (POST /applications/{application_id}/conversation) in backend/src/api/conversations.py that triggers agent and returns stream URL
- [X] T035 [US1] Implement application creation endpoint (POST /applications) in backend/src/api/applications.py
- [X] T036 [US1] Implement get application endpoint (GET /applications/{application_id}) in backend/src/api/applications.py
- [X] T037 [US1] Implement list applications endpoint (GET /applications) in backend/src/api/applications.py
- [X] T038 [US1] Implement confirm requirements endpoint (POST /applications/{application_id}/confirm-requirements) in backend/src/api/applications.py
- [X] T039 [US1] Create frontend Login page component in fe/src/pages/Login.tsx
- [X] T040 [US1] Create frontend Register page component in fe/src/pages/Register.tsx
- [X] T041 [US1] Create frontend Dashboard page component in fe/src/pages/Dashboard.tsx with application list
- [X] T042 [US1] Setup CopilotKit provider and configuration in fe/src/App.tsx
- [X] T043 [US1] Create Conversation component using CopilotKit in fe/src/components/Conversation/Conversation.tsx
- [X] T044 [US1] Implement SSE client for streaming agent events in fe/src/services/sse.ts
- [X] T045 [US1] Integrate SSE client with CopilotKit in fe/src/components/Conversation/Conversation.tsx
- [X] T046 [US1] Create application creation UI in fe/src/components/Application/CreateApplication.tsx
- [X] T047 [US1] Create application list UI in fe/src/components/Application/ApplicationList.tsx
- [X] T048 [US1] Implement routing with React Router in fe/src/App.tsx (Login, Register, Dashboard routes)
- [X] T049 [US1] Create authentication context and hooks in fe/src/hooks/useAuth.ts for session management
- [X] T050 [US1] Add error handling and user-friendly error messages in conversation interface

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can register, login, create applications, have conversations with the AI agent, and confirm requirements.

---

## Phase 4: User Story 3 - View Generated Code Structure (Priority: P1)

**Goal**: Users can view the complete file structure and contents of their generated application through an integrated code editor interface. The interface displays a file tree showing all directories and files within the container, and users can navigate and read any file's contents.

**Independent Test**: Can be fully tested by generating a simple application, verifying that the file tree displays all generated files and directories, and confirming that users can click on any file to view its complete contents in the editor pane.

### Implementation for User Story 3

- [X] T051 [P] [US3] Create Container model in backend/src/models/container.py with application_id, container_id, image, status, port, resource_limits, created_at, updated_at
- [X] T052 [US3] Create container service in backend/src/services/container/container_service.py (create, get, update container metadata)
- [X] T053 [US3] Implement Docker client wrapper in backend/src/containers/docker_client.py using Docker SDK
- [X] T054 [US3] Implement file tree retrieval from container in backend/src/containers/file_tree.py (list directories and files)
- [X] T055 [US3] Implement file content retrieval from container in backend/src/containers/file_content.py (read file contents)
- [X] T056 [US3] Implement endpoint to get file tree (GET /applications/{application_id}/files) in backend/src/api/applications.py
- [X] T057 [US3] Implement endpoint to get file content (GET /applications/{application_id}/files/{file_path}) in backend/src/api/applications.py
- [X] T058 [US3] Create CodeEditor component with file tree in fe/src/components/CodeEditor/CodeEditor.tsx
- [X] T059 [US3] Implement file tree display with expand/collapse in fe/src/components/CodeEditor/FileTree.tsx
- [X] T060 [US3] Implement file content viewer with syntax highlighting in fe/src/components/CodeEditor/FileViewer.tsx
- [X] T061 [US3] Integrate CodeEditor component into Dashboard page in fe/src/pages/Dashboard.tsx
- [X] T062 [US3] Add file tree auto-refresh when files change in fe/src/components/CodeEditor/CodeEditor.tsx
- [X] T063 [US3] Implement file navigation (click to view, directory expand/collapse) in fe/src/components/CodeEditor/FileTree.tsx

**Checkpoint**: At this point, User Story 3 should be fully functional. Users can view file structure and file contents from containers through the code editor interface.

---

## Phase 5: User Story 2 - Automatic Code Generation and Execution (Priority: P2)

**Goal**: After requirements are confirmed, the system automatically generates the necessary code for the application, packages it for container execution, runs it in an isolated environment, and makes the running application accessible through the platform's interface.

**Independent Test**: Can be fully tested by providing the system with a complete, pre-defined set of requirements (bypassing the conversation interface), verifying code generation, container execution, and that the running app is accessible and functional.

### Implementation for User Story 2

- [X] T064 [US2] Create code generation sub-agent in backend/src/agents/code_gen/agent.py using LangGraph with code generation, file operations, and command execution nodes
- [X] T065 [US2] Implement file operation tools for agent in backend/src/agents/tools/file_ops.py (create file, write file, read file, list directory)
- [X] T066 [US2] Implement command execution tools for agent in backend/src/agents/tools/command_exec.py (execute command in container, get command output)
- [X] T067 [US2] Implement container command execution in backend/src/containers/exec.py (execute commands via Docker SDK)
- [X] T068 [US2] Implement container creation and lifecycle management in backend/src/services/container/container_lifecycle.py (create, start, stop, remove containers)
- [X] T069 [US2] Implement code generation workflow that creates container, generates files, installs dependencies, starts dev server in backend/src/services/agent/code_gen_service.py
- [X] T070 [US2] Update app_creator agent to invoke code_gen sub-agent after requirements confirmation in backend/src/agents/app_creator/agent.py
- [X] T071 [US2] Implement container file operations (copy files into container) in backend/src/containers/file_ops.py
- [X] T072 [US2] Implement application status tracking and updates in backend/src/services/application/application_service.py (update status: generating, deploying, running, error)
- [X] T073 [US2] Implement container network and port management in backend/src/services/container/container_network.py (expose ports, create networks)
- [X] T074 [US2] Implement preview URL generation and management in backend/src/services/container/preview_url.py
- [X] T075 [US2] Update Application model with container_id, preview_url, port, last_deployed_at in backend/src/models/application.py
- [X] T076 [US2] Implement endpoint to get preview information (GET /applications/{application_id}/preview) in backend/src/api/applications.py
- [X] T077 [US2] Create AppPreview component with iframe in fe/src/components/AppPreview/AppPreview.tsx
- [X] T078 [US2] Integrate AppPreview component into Dashboard page in fe/src/pages/Dashboard.tsx
- [X] T079 [US2] Implement preview URL loading and error handling in fe/src/components/AppPreview/AppPreview.tsx
- [X] T080 [US2] Add status indicators for code generation and deployment in fe/src/components/Application/ApplicationStatus.tsx
- [X] T081 [US2] Implement real-time status updates via SSE in conversation stream for code generation progress in backend/src/agents/code_gen/agent.py
- [X] T082 [US2] Display tool_call and tool_call_result events in conversation UI for code generation operations in fe/src/components/Conversation/Conversation.tsx
- [X] T083 [US2] Add error handling for code generation failures with user-friendly messages in backend/src/services/agent/code_gen_service.py
- [X] T084 [US2] Implement container resource limits (memory, CPU) configuration in backend/src/services/container/container_lifecycle.py
- [X] T085 [US2] Implement container cleanup on application deletion in backend/src/services/application/application_service.py

**Checkpoint**: At this point, User Story 2 should be fully functional. Users can confirm requirements, system generates code, runs it in containers, and users can preview running applications.

---

## Phase 6: User Story 4 - Iterative Refinement Through Conversation (Priority: P3)

**Goal**: Users can continue the conversation after seeing their running application to request changes, additions, or refinements. The system updates the code accordingly and redeploys the application with the changes.

**Independent Test**: Can be fully tested by starting with an existing running application, having a user request specific changes through conversation, and verifying that the changes are implemented and the updated application runs correctly.

### Implementation for User Story 4

- [ ] T086 [US4] Update app_creator agent to handle refinement requests for existing applications in backend/src/agents/app_creator/agent.py
- [ ] T087 [US4] Implement code modification workflow in code_gen agent to update existing files instead of creating new ones in backend/src/agents/code_gen/agent.py
- [ ] T088 [US4] Implement file update operations in backend/src/agents/tools/file_ops.py (update file, delete file)
- [ ] T089 [US4] Implement application redeployment workflow that preserves existing functionality in backend/src/services/agent/code_gen_service.py
- [ ] T090 [US4] Update conversation service to handle continuation of existing conversations in backend/src/services/conversation/conversation_service.py
- [ ] T091 [US4] Implement conflict detection for conflicting change requests in backend/src/agents/app_creator/agent.py
- [ ] T092 [US4] Add validation to prevent breaking changes in backend/src/services/agent/code_gen_service.py
- [ ] T093 [US4] Update application status management for redeployment scenarios in backend/src/services/application/application_service.py
- [ ] T094 [US4] Implement container restart and code update workflow in backend/src/services/container/container_lifecycle.py
- [ ] T095 [US4] Update frontend conversation UI to support continued conversations for existing applications in fe/src/components/Conversation/Conversation.tsx
- [ ] T096 [US4] Add UI indicators for application updates and redeployment in fe/src/components/Application/ApplicationStatus.tsx

**Checkpoint**: At this point, User Story 4 should be fully functional. Users can request changes to existing applications, system updates code and redeploys, maintaining existing functionality while incorporating new requirements.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T097 [P] Update application documentation in README.md with usage instructions
- [ ] T098 [P] Add API documentation comments to all endpoints in backend/src/api/
- [ ] T099 Code cleanup and refactoring across backend and frontend
- [ ] T100 Performance optimization for SSE streaming and agent responses
- [ ] T101 Security hardening (input validation, sanitization, rate limiting)
- [ ] T102 Implement container timeout and automatic cleanup in backend/src/services/container/container_lifecycle.py
- [ ] T103 Add logging for all agent operations and container activities in backend/src/utils/logger.py
- [ ] T104 Implement conversation message limits and archiving in backend/src/services/conversation/conversation_service.py
- [ ] T105 Add accessibility features (keyboard navigation, screen reader support) in frontend components
- [ ] T106 Implement error recovery and retry mechanisms for container operations
- [ ] T107 Validate quickstart.md instructions by following them in a clean environment
- [ ] T108 Add monitoring and health check endpoints in backend/src/api/health.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (Phase 3): Can start after Foundational - No dependencies on other stories
  - User Story 3 (Phase 4): Can start after Foundational - Can proceed independently but benefits from seeing code structure
  - User Story 2 (Phase 5): Depends on User Story 1 for requirements confirmation flow
  - User Story 4 (Phase 6): Depends on User Story 2 for existing application refinement
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **MVP CANDIDATE**
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Independent but needs containers from US2 for full functionality
- **User Story 2 (P2)**: Depends on User Story 1 for requirements confirmation - Needs container infrastructure
- **User Story 4 (P3)**: Depends on User Story 2 for existing applications to refine

### Within Each User Story

- Models before services
- Services before endpoints/agents
- Backend models/services before API endpoints
- API endpoints before frontend integration
- Core implementation before UI polish

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Foundational tasks marked [P] can run in parallel (models, endpoints, services in different files)
- User Story 1 and User Story 3 models can be created in parallel after Foundational
- Frontend and backend work within a story can proceed in parallel once API contracts are defined
- Different user stories can be worked on in parallel by different team members after dependencies are met

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create Application model in backend/src/models/application.py"
Task: "Create Conversation model in backend/src/models/conversation.py"

# Launch all API endpoints for User Story 1 together (after services):
Task: "Implement application creation endpoint in backend/src/api/applications.py"
Task: "Implement conversation streaming endpoint in backend/src/api/conversations.py"
Task: "Implement send message endpoint in backend/src/api/conversations.py"
Task: "Implement confirm requirements endpoint in backend/src/api/applications.py"

# Launch all frontend components for User Story 1 together:
Task: "Create Login page component in fe/src/pages/Login.tsx"
Task: "Create Register page component in fe/src/pages/Register.tsx"
Task: "Create Conversation component using CopilotKit in fe/src/components/Conversation/Conversation.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Conversational Requirements Gathering)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - Users can create applications and have conversations

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 → Test independently → Deploy/Demo (Code viewing - but needs containers from US2 for real data)
4. Add User Story 2 → Test independently → Deploy/Demo (Full code generation and execution)
5. Add User Story 4 → Test independently → Deploy/Demo (Iterative refinement)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend agent + API)
   - Developer B: User Story 1 (frontend UI)
   - Developer C: User Story 3 (code editor - can work independently)
3. After User Story 1 completes:
   - Developer A: User Story 2 (code generation agent)
   - Developer B: User Story 2 (container management)
   - Developer C: User Story 2 (preview UI)
4. After User Story 2 completes:
   - Team: User Story 4 (iterative refinement)
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- User Story 2 depends on User Story 1 for requirements confirmation flow
- User Story 3 can start independently but needs containers from US2 for full functionality
- User Story 4 depends on User Story 2 for existing applications
- MVP scope: User Story 1 only (conversational requirements gathering)


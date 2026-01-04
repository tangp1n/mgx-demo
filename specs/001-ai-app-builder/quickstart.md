# Quick Start Guide: AI-Powered Conversational App Builder Platform

**Date**: 2026-01-04
**Feature**: 001-ai-app-builder

This guide provides instructions for setting up and running the development environment for the AI-powered conversational app builder platform.

## Prerequisites

- **Python 3.11+**: Required for backend development
- **Node.js 18+**: Required for frontend development
- **Docker**: Required for container execution (Docker Desktop or Docker Engine)
- **MongoDB**: Required for data storage (local installation or MongoDB Atlas)
- **Git**: For version control

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd mgx-demo
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and set:
# - MONGODB_URL=mongodb://localhost:27017/appbuilder
# - SECRET_KEY=<generate-a-secret-key>
# - LLM_API_KEY=<your-llm-api-key>
# - LLM_PROVIDER=openai  # or anthropic
# - LLM_MODEL=gpt-4  # or claude-3-opus

# Run database migrations (if applicable)
# python scripts/migrate.py

# Start backend server
uvicorn src.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd fe

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env and set:
# - REACT_APP_API_URL=http://localhost:8000/api/v1

# Start development server
npm start
```

Frontend will be available at `http://localhost:3000`

### 4. MongoDB Setup

**Option A: Local MongoDB**

```bash
# Install MongoDB (macOS)
brew install mongodb-community
brew services start mongodb-community

# Install MongoDB (Ubuntu/Debian)
sudo apt-get install mongodb
sudo systemctl start mongodb

# Install MongoDB (Windows)
# Download and install from https://www.mongodb.com/try/download/community
```

**Option B: MongoDB Atlas (Cloud)**

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Get connection string
4. Update `MONGODB_URL` in backend `.env` file

### 5. Docker Setup

**Option A: Docker Desktop**

1. Download and install from https://www.docker.com/products/docker-desktop
2. Start Docker Desktop
3. Verify: `docker ps`

**Option B: Docker Engine (Linux)**

```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
```

## Running the Application

### 1. Start Services

**Terminal 1: MongoDB**
```bash
# If using local MongoDB
mongod
```

**Terminal 2: Backend**
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Terminal 3: Frontend**
```bash
cd fe
npm start
```

**Terminal 4: Docker (if not running)**
```bash
# Docker Desktop should auto-start, or:
docker ps  # Verify Docker is running
```

### 2. Access the Application

1. Open browser to `http://localhost:3000`
2. Register a new account or login
3. Create a new application
4. Start a conversation to describe your app requirements

## Development Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Run with hot reload
uvicorn src.main:app --reload

# Format code
black src/

# Lint code
flake8 src/
```

### Frontend Development

```bash
cd fe

# Run tests
npm test

# Build for production
npm run build

# Format code
npm run format

# Lint code
npm run lint
```

### Database Management

```bash
# Connect to MongoDB (local)
mongosh

# Or use MongoDB Compass (GUI)
# Download from https://www.mongodb.com/products/compass
```

## Configuration

### Backend Configuration (`backend/.env`)

```env
# Database
MONGODB_URL=mongodb://localhost:27017/appbuilder

# Security
SECRET_KEY=your-secret-key-here
SESSION_EXPIRY_HOURS=24

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4

# Container Configuration
DOCKER_NETWORK=appbuilder-network
CONTAINER_MEMORY_LIMIT_MB=512
CONTAINER_CPU_LIMIT=0.5
CONTAINER_TIMEOUT_MINUTES=60

# Server
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### Frontend Configuration (`fe/.env`)

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_SSE_URL=http://localhost:8000/api/v1
```

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=src tests/
```

### Frontend Tests

```bash
cd fe

# Run all tests
npm test

# Run with coverage
npm test -- --coverage
```

## Troubleshooting

### MongoDB Connection Issues

- Verify MongoDB is running: `mongosh` or `docker ps` (if using Docker)
- Check connection string in `.env`
- Verify network/firewall settings

### Docker Issues

- Verify Docker is running: `docker ps`
- Check Docker daemon: `docker info`
- Verify user permissions (Linux): `sudo usermod -aG docker $USER` then logout/login

### Port Conflicts

- Backend (8000): Change in `backend/.env` or use `--port` flag
- Frontend (3000): Change in `fe/.env` or use `PORT=3001 npm start`
- MongoDB (27017): Change in MongoDB config and `.env`

### LLM API Issues

- Verify API key is set correctly in `.env`
- Check API key permissions and limits
- Verify network connectivity to LLM provider

## Next Steps

1. Review API documentation at `http://localhost:8000/docs` (Swagger UI)
2. Read the [data model documentation](./data-model.md)
3. Review [API contracts](./contracts/api.yaml)
4. Check [implementation plan](./plan.md) for architecture details

## Production Deployment

For production deployment:

1. Set `DEBUG=false` in backend configuration
2. Use environment-specific MongoDB (e.g., MongoDB Atlas)
3. Configure proper security (HTTPS, CORS, rate limiting)
4. Set up container orchestration (Kubernetes, Docker Swarm)
5. Configure monitoring and logging
6. Set up CI/CD pipeline
7. Configure backup and disaster recovery

See deployment documentation for detailed production setup instructions.


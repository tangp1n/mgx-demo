# AI-Powered Conversational App Builder Platform

A platform where users create applications through natural language dialogue with an AI agent. The system understands requirements, generates code, runs applications in isolated containers, and provides real-time preview capabilities.

## Architecture

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React with TypeScript
- **Database**: MongoDB
- **AI/LLM**: LangGraph, LangChain with OpenAI/Anthropic
- **Containerization**: Docker
- **Real-time Communication**: Server-Sent Events (SSE)

## Project Structure

```
.
├── backend/          # Python FastAPI backend
│   ├── src/         # Source code
│   └── tests/       # Tests
├── fe/              # React frontend
│   ├── src/         # Source code
│   └── public/      # Static assets
└── specs/           # Specification and design documents
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- MongoDB (local or Atlas)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and configure: MONGODB_URL, SECRET_KEY, LLM_API_KEY, etc.

# Start backend server
uvicorn src.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd fe

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env and set REACT_APP_API_URL

# Start development server
npm start
```

Frontend will be available at `http://localhost:3000`

## Development

### Backend

```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Format code
black src/

# Lint code
flake8 src/
```

### Frontend

```bash
cd fe

# Run tests
npm test

# Format code
npm run format

# Lint code
npm run lint
```

## Documentation

- [Specification](./specs/001-ai-app-builder/spec.md)
- [Implementation Plan](./specs/001-ai-app-builder/plan.md)
- [Data Model](./specs/001-ai-app-builder/data-model.md)
- [API Contracts](./specs/001-ai-app-builder/contracts/api.yaml)
- [Quick Start Guide](./specs/001-ai-app-builder/quickstart.md)

## License

[Add license information]


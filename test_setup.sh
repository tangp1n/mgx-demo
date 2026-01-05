#!/bin/bash

# AI App Builder - Setup Test Script
# This script checks if all prerequisites are met before running the application

echo "========================================="
echo "AI App Builder - Setup Test"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check results
all_good=true

# 1. Check Python
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $version${NC}"
else
    echo -e "${RED}✗ Python not found${NC}"
    all_good=false
fi

# 2. Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    version=$(node --version)
    echo -e "${GREEN}✓ Node.js $version${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    all_good=false
fi

# 3. Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    version=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "${GREEN}✓ Docker $version${NC}"

    # Check if Docker daemon is running
    echo -n "Checking Docker daemon... "
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓ Docker daemon is running${NC}"
    else
        echo -e "${RED}✗ Docker daemon is NOT running${NC}"
        echo -e "${YELLOW}  Please start Docker Desktop or Docker daemon${NC}"
        all_good=false
    fi
else
    echo -e "${RED}✗ Docker not found${NC}"
    all_good=false
fi

# 4. Check MongoDB
echo -n "Checking MongoDB... "
if command -v mongosh &> /dev/null || command -v mongo &> /dev/null; then
    echo -e "${GREEN}✓ MongoDB client found${NC}"

    # Try to connect to MongoDB
    echo -n "Checking MongoDB connection... "
    if mongosh --eval "db.adminCommand('ping')" --quiet mongodb://localhost:27017 &> /dev/null || \
       mongo --eval "db.adminCommand('ping')" --quiet mongodb://localhost:27017 &> /dev/null; then
        echo -e "${GREEN}✓ MongoDB is running${NC}"
    else
        echo -e "${RED}✗ MongoDB is NOT running${NC}"
        echo -e "${YELLOW}  Please start MongoDB: mongod${NC}"
        all_good=false
    fi
else
    echo -e "${YELLOW}⚠ MongoDB client not found (using MongoDB Atlas is OK)${NC}"
fi

echo ""
echo "========================================="
echo "Configuration Files"
echo "========================================="
echo ""

# 5. Check backend .env
echo -n "Checking backend/.env... "
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓ Found${NC}"

    # Check required variables
    required_vars=("MONGODB_URL" "SECRET_KEY" "LLM_PROVIDER" "OPENAI_API_KEY")
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" backend/.env; then
            echo -e "  ${GREEN}✓ $var${NC}"
        else
            echo -e "  ${RED}✗ $var missing${NC}"
            all_good=false
        fi
    done
else
    echo -e "${RED}✗ Not found${NC}"
    all_good=false
fi

# 6. Check frontend .env
echo -n "Checking fe/.env... "
if [ -f "fe/.env" ]; then
    echo -e "${GREEN}✓ Found${NC}"

    if grep -q "^REACT_APP_API_URL=" fe/.env; then
        echo -e "  ${GREEN}✓ REACT_APP_API_URL${NC}"
    else
        echo -e "  ${RED}✗ REACT_APP_API_URL missing${NC}"
        all_good=false
    fi
else
    echo -e "${RED}✗ Not found${NC}"
    all_good=false
fi

echo ""
echo "========================================="
echo "Dependencies"
echo "========================================="
echo ""

# 7. Check Python virtual environment
echo -n "Checking Python venv... "
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found${NC}"
    echo -e "${YELLOW}  Run: cd backend && python3 -m venv venv${NC}"
fi

# 8. Check Node modules
echo -n "Checking Node modules... "
if [ -d "fe/node_modules" ]; then
    echo -e "${GREEN}✓ Node modules installed${NC}"
else
    echo -e "${YELLOW}⚠ Node modules not found${NC}"
    echo -e "${YELLOW}  Run: cd fe && npm install${NC}"
fi

echo ""
echo "========================================="

if [ "$all_good" = true ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo ""
    echo "You can now start the application:"
    echo ""
    echo "Terminal 1 - Start MongoDB (if not using Atlas):"
    echo "  mongod"
    echo ""
    echo "Terminal 2 - Start Backend:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  uvicorn src.main:app --reload --port 8000"
    echo ""
    echo "Terminal 3 - Start Frontend:"
    echo "  cd fe"
    echo "  npm start"
    echo ""
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi

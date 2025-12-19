#!/bin/bash

set -e  # Exit on error

echo "========================================"
echo "Visibility Simulator - Installation"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed.${NC}"
    echo "Please install Python 3.11 from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}ERROR: Python 3.8 or higher required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check/Install Node.js
echo ""
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install node
        else
            echo -e "${RED}ERROR: Homebrew not found. Please install Node.js manually:${NC}"
            echo "Visit: https://nodejs.org/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command -v yum &> /dev/null; then
            curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
            sudo yum install -y nodejs
        else
            echo -e "${RED}ERROR: Could not install Node.js automatically.${NC}"
            echo "Please install Node.js manually: https://nodejs.org/"
            exit 1
        fi
    fi
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: npm not found after Node.js installation${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm $NPM_VERSION${NC}"

# Check C++ compiler
echo ""
echo "Checking C++ compiler..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v clang++ &> /dev/null; then
        echo -e "${YELLOW}Installing Xcode Command Line Tools...${NC}"
        xcode-select --install
        echo "Please complete the Xcode installation and run this script again."
        exit 1
    fi
    echo -e "${GREEN}✓ clang++ found${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v g++ &> /dev/null; then
        echo -e "${YELLOW}Installing build tools...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y build-essential python3-dev
        elif command -v yum &> /dev/null; then
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y python3-devel
        fi
    fi
    echo -e "${GREEN}✓ g++ found${NC}"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --break-system-packages Flask==3.1.0 flask-cors==6.0.1 Werkzeug==3.1.3 2>/dev/null || \
pip3 install Flask==3.1.0 flask-cors==6.0.1 Werkzeug==3.1.3 

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${RED}ERROR: Failed to install Python dependencies${NC}"
    exit 1
fi

# Install React dependencies
echo ""
echo "Installing React dependencies..."
if [ ! -d "frontend" ]; then
    echo -e "${RED}ERROR: frontend directory not found${NC}"
    exit 1
fi

cd frontend
npm install
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ React dependencies installed${NC}"
else
    echo -e "${RED}ERROR: Failed to install React dependencies${NC}"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "========================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "========================================"
echo ""
echo "To start the application:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    python3 app.py"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    npm start"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
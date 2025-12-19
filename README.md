# Visibility Simulator - Installation Guide

A React + Flask application for computing and visualizing visibility polygons, isovists, and allocentric visibility with sensitivity analysis.

## Prerequisites

### Required Software

1. **Python 3.11** (or 3.8+)
   - Download: https://www.python.org/downloads/
   - **Important**: On Windows, check "Add Python to PATH" during installation

2. **Node.js 14+** (includes npm)
   - Download: https://nodejs.org/
   - Recommended: LTS version
---

## Quick Install (Automated)

### macOS / Linux
```bash
chmod +x install.sh
./install.sh
```

### Windows
```cmd
install.bat
```

The installation script will:
- Check Python, Node.js, and C++ compiler
- Install Python dependencies (Flask, Werkzeug)
- Install React dependencies

---

## Manual Installation

If the automated script fails, follow these steps:

### 1. Install Prerequisites

#### Install Python 3.11

**macOS**:
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-dev python3-pip
```

**Windows**:
- Download from https://www.python.org/downloads/
- Run installer and check "Add Python to PATH"

#### Install Node.js

**macOS**:
```bash
brew install node
```

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows**:
- Download from https://nodejs.org/
- Run the installer

#### Install C++ Compiler

**macOS**:
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

**Windows**:
1. Download Visual Studio Build Tools 2022: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
2. Run installer
3. Select "Desktop development with C++" workload
4. Install

### 2. Install Python Dependencies
```bash
# macOS/Linux
pip3 install Flask==3.1.0 flask-cors==6.0.1 Werkzeug==3.1.3 

# Windows
pip install Flask==3.1.0 flask-cors==6.0.1 Werkzeug==3.1.3 
```
### 3. Install React Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### Development Mode (with hot reload)

**Terminal 1 - Start Backend:**
```bash
# macOS/Linux
python3 app.py

# Windows
python app.py
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm start
```

The application will open automatically at **http://localhost:3000**

---

## Troubleshooting

### Python Module Not Found

**Error**: `ModuleNotFoundError: No module named 'visibility_polygon'`

**Solution**:
1. Verify the `.so` or `.pyd` file exists in the project root
2. Check Python version matches (3.11.x)
3. If the problem persists, contact brn.cntrll at gmail

### Port Already in Use

**Error**: `Address already in use: 5001` or `3000`

**Solution**:
- Kill existing process or change port in `app.py`:
```python
  app.run(debug=True, port=5002)
```

### React Dependencies Install Fails

**Error**: `npm ERR! EACCES: permission denied`

**Solution** (macOS/Linux):
```bash
sudo chown -R $(whoami) ~/.npm
cd frontend
npm install
```

### Missing Dependencies

If you get import errors, install missing packages:
```bash
pip3 install <package-name>
```
---

## Usage

1. **Import SVG**: Click "Import SVG" to load a floor plan
2. **Set Point of View**: Right-click on canvas to place viewpoint
3. **Assign Features**: 
   - Left-click an obstacle to select it
   - Click "Assign Feature"
   - Toggle between Occlude/Sensitivity modes
   - Adjust visibility sliders
4. **Compute Heatmaps**: Generate visibility analysis across the floor plan

---

## System Requirements

- **OS**: macOS 10.14+, Linux (Ubuntu 18.04+), Windows 10+
- **RAM**: 4GB minimum, 8GB recommended
- **Python**: 3.11 recommended
- **Node.js**: 14+
- **Disk Space**: 500MB for dependencies

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Verify all prerequisites are installed correctly
3. Try the manual installation steps
4. Check that Python version is 3.8+: `python3 --version`
5. Check that Node.js is installed: `node --version`

---

## License

[LICENSE.md](LICENSE.md)

## Contact

brn.cntrll at gmail
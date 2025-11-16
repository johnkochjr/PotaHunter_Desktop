#!/bin/bash
# Build script for creating POTA Hunter executable

echo "======================================"
echo "POTA Hunter - Build Executable"
echo "======================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
    echo ""
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/
echo ""

# Build executable
echo "Building executable..."
echo "This may take a few minutes..."
echo ""

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Building for macOS..."
    echo "Using fixed spec to avoid PySide6 symlink conflicts..."
    PYTHONPATH=src pyinstaller --clean PotaHunter-fixed.spec

    if [ $? -eq 0 ]; then
        echo ""
        echo "Creating launcher script..."
        cat > dist/launch_potahunter.sh << 'EOF'
#!/bin/bash
# Launcher script for POTA Hunter
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Launch the application
"${SCRIPT_DIR}/PotaHunter.app/Contents/MacOS/PotaHunter"
EOF
        chmod +x dist/launch_potahunter.sh

        echo ""
        echo "======================================"
        echo "Build successful!"
        echo "======================================"
        echo ""
        echo "Your application is ready in the dist/ folder:"
        echo "  - PotaHunter.app (app bundle)"
        echo "  - launch_potahunter.sh (launcher script)"
        echo ""
        echo "To run:"
        echo "  ./dist/launch_potahunter.sh"
        echo "  or: ./dist/PotaHunter.app/Contents/MacOS/PotaHunter"
        echo ""
        echo "To distribute to testers:"
        echo "  1. Zip the dist folder: zip -r PotaHunter-macOS.zip dist/"
        echo "  2. Send PotaHunter-macOS.zip to testers"
        echo "  3. Testers should unzip and run: ./dist/launch_potahunter.sh"
        echo ""
    else
        echo ""
        echo "Build failed. Check the output above for errors."
        exit 1
    fi

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Building for Linux..."
    pyinstaller PotaHunter.spec

    if [ $? -eq 0 ]; then
        echo ""
        echo "======================================"
        echo "Build successful!"
        echo "======================================"
        echo ""
        echo "Your application is ready:"
        echo "  Linux executable: dist/PotaHunter/PotaHunter"
        echo ""
        echo "To run:"
        echo "  ./dist/PotaHunter/PotaHunter"
        echo ""
    else
        echo ""
        echo "Build failed. Check the output above for errors."
        exit 1
    fi

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Building for Windows..."
    pyinstaller PotaHunter.spec

    if [ $? -eq 0 ]; then
        echo ""
        echo "======================================"
        echo "Build successful!"
        echo "======================================"
        echo ""
        echo "Your application is ready:"
        echo "  Windows executable: dist\\PotaHunter\\PotaHunter.exe"
        echo ""
        echo "To run:"
        echo "  dist\\PotaHunter\\PotaHunter.exe"
        echo ""
    else
        echo ""
        echo "Build failed. Check the output above for errors."
        exit 1
    fi
fi

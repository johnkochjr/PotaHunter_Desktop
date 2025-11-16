@echo off
REM Build script for creating POTA Hunter executable on Windows

echo ======================================
echo POTA Hunter - Build Executable
echo ======================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM Build executable
echo Building executable...
echo This may take a few minutes...
echo.

pyinstaller PotaHunter.spec

if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo Build successful!
    echo ======================================
    echo.
    echo Your application is ready:
    echo   Windows executable: dist\PotaHunter\PotaHunter.exe
    echo.
    echo To run:
    echo   dist\PotaHunter\PotaHunter.exe
    echo.
    echo You can distribute the entire dist\PotaHunter folder
    echo.
) else (
    echo.
    echo Build failed. Check the output above for errors.
    exit /b 1
)

pause

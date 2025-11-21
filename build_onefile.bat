@echo off
REM Build script for creating POTA Hunter single-file executable on Windows

echo ======================================
echo POTA Hunter - Build Single-File Executable
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
echo Building single-file executable...
echo This may take a few minutes...
echo NOTE: Single-file executables are slower to start but easier to distribute.
echo.

pyinstaller PotaHunter-onefile.spec

if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo Build successful!
    echo ======================================
    echo.
    echo Your single-file application is ready:
    echo   Windows executable: dist\PotaHunter.exe
    echo.
    echo To run:
    echo   dist\PotaHunter.exe
    echo.
    echo You can distribute just this ONE file - no folders needed!
    echo.
    echo NOTE: On first run, it will extract files to a temp folder,
    echo       so startup may take a few seconds.
    echo.
) else (
    echo.
    echo Build failed. Check the output above for errors.
    exit /b 1
)

pause

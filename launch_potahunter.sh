#!/bin/bash
# Launcher script for POTA Hunter
# This script launches the POTA Hunter application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch the application
"${SCRIPT_DIR}/dist/PotaHunter.app/Contents/MacOS/PotaHunter"

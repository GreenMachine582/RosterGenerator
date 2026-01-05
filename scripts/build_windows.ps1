$ErrorActionPreference = "Stop"

# From repo root
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pyinstaller

# Clean previous builds
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

# Build: windowed (no console)
pyinstaller `
  --clean --noconfirm `
  --name "RosterGenerator-Setup" `
  --onedir `
  --windowed `
  src/roster_generator/__main__.py

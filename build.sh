#!/usr/bin/env bash
# Render build script for PawRes
# This runs during the build phase on Render

set -o errexit  # Exit on error

echo "=== PawRes Build Script ==="

# Install Python dependencies (using the Render-specific requirements)
pip install --upgrade pip
pip install -r requirements-render.txt

# Create required storage directories
echo "Creating storage directories..."
mkdir -p app/storage/data
mkdir -p app/storage/uploads
mkdir -p app/storage/temp
mkdir -p app/storage/ai_models
mkdir -p app/uploads
mkdir -p app/assets/icons
mkdir -p app/assets/images
mkdir -p app/assets/templates
mkdir -p app/assets/exports

echo "=== Build complete ==="

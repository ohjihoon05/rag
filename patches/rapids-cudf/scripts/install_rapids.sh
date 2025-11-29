#!/bin/bash
# RAPIDS cuDF Installation Script for RAGFlow
# This script installs RAPIDS cuDF inside the RAGFlow Docker container
#
# Requirements:
#   - Linux host with NVIDIA GPU
#   - CUDA 12.x compatible driver
#   - Docker with nvidia-container-toolkit
#
# Usage:
#   ./install_rapids.sh [container_name]
#
# Default container: ragflow-server

set -e

CONTAINER_NAME="${1:-ragflow-server}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "RAPIDS cuDF Installation for RAGFlow"
echo "=============================================="
echo "Target container: $CONTAINER_NAME"
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container '$CONTAINER_NAME' is not running"
    echo "Please start RAGFlow first: docker compose up -d"
    exit 1
fi

# Check GPU availability in container
echo "[1/5] Checking GPU availability..."
GPU_CHECK=$(docker exec "$CONTAINER_NAME" python3 -c "
import subprocess
result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], capture_output=True, text=True)
if result.returncode == 0:
    print('GPU:', result.stdout.strip())
else:
    print('NO_GPU')
" 2>&1)

if echo "$GPU_CHECK" | grep -q "NO_GPU"; then
    echo "ERROR: No GPU detected in container"
    echo "Make sure your Docker container has GPU access"
    exit 1
fi
echo "$GPU_CHECK"

# Check CUDA version
echo ""
echo "[2/5] Checking CUDA version..."
CUDA_VERSION=$(docker exec "$CONTAINER_NAME" python3 -c "
import subprocess
result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
if result.returncode == 0:
    import re
    match = re.search(r'release (\d+\.\d+)', result.stdout)
    if match:
        print(match.group(1))
    else:
        print('UNKNOWN')
else:
    print('NOT_FOUND')
" 2>&1)

echo "CUDA Version: $CUDA_VERSION"

# Determine cuDF package based on CUDA version
if [[ "$CUDA_VERSION" == "12."* ]]; then
    CUDF_PACKAGE="cudf-cu12"
elif [[ "$CUDA_VERSION" == "11."* ]]; then
    CUDF_PACKAGE="cudf-cu11"
else
    echo "WARNING: Unknown CUDA version, defaulting to CUDA 12"
    CUDF_PACKAGE="cudf-cu12"
fi

# Install cuDF
echo ""
echo "[3/5] Installing RAPIDS cuDF ($CUDF_PACKAGE)..."
echo "This may take several minutes..."

docker exec "$CONTAINER_NAME" pip install "$CUDF_PACKAGE" \
    --extra-index-url=https://pypi.nvidia.com \
    --quiet

# Verify installation
echo ""
echo "[4/5] Verifying cuDF installation..."
VERIFY=$(docker exec "$CONTAINER_NAME" python3 -c "
try:
    import cudf
    print(f'cuDF version: {cudf.__version__}')
    print('Installation successful!')
except ImportError as e:
    print(f'ERROR: {e}')
    exit(1)
" 2>&1)

echo "$VERIFY"

if echo "$VERIFY" | grep -q "ERROR"; then
    echo "cuDF installation failed"
    exit 1
fi

# Backup original excel_parser.py and apply patch
echo ""
echo "[5/5] Applying Excel parser patch..."

# Create backup directory in container
docker exec "$CONTAINER_NAME" mkdir -p /ragflow/deepdoc/parser/backup

# Backup original file
docker exec "$CONTAINER_NAME" cp /ragflow/deepdoc/parser/excel_parser.py \
    /ragflow/deepdoc/parser/backup/excel_parser.py.original

# Copy patched file
docker cp "$PATCH_DIR/excel_parser_cudf.py" \
    "$CONTAINER_NAME:/ragflow/deepdoc/parser/excel_parser.py"

echo ""
echo "=============================================="
echo "Installation Complete!"
echo "=============================================="
echo ""
echo "GPU-accelerated Excel parsing is now enabled."
echo ""
echo "To verify:"
echo "  docker exec $CONTAINER_NAME python3 -c \"from deepdoc.parser.excel_parser import get_acceleration_status; print(get_acceleration_status())\""
echo ""
echo "To rollback:"
echo "  ./rollback_rapids.sh $CONTAINER_NAME"
echo ""
echo "NOTE: Restart RAGFlow services for changes to take effect:"
echo "  docker compose restart ragflow-server"

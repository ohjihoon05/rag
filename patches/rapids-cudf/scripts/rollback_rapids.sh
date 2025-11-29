#!/bin/bash
# RAPIDS cuDF Rollback Script for RAGFlow
# Restores the original Excel parser without cuDF acceleration
#
# Usage:
#   ./rollback_rapids.sh [container_name]
#
# Default container: ragflow-server

set -e

CONTAINER_NAME="${1:-ragflow-server}"

echo "=============================================="
echo "RAPIDS cuDF Rollback for RAGFlow"
echo "=============================================="
echo "Target container: $CONTAINER_NAME"
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container '$CONTAINER_NAME' is not running"
    exit 1
fi

# Check if backup exists
BACKUP_EXISTS=$(docker exec "$CONTAINER_NAME" bash -c "
if [ -f /ragflow/deepdoc/parser/backup/excel_parser.py.original ]; then
    echo 'YES'
else
    echo 'NO'
fi
" 2>&1)

if [ "$BACKUP_EXISTS" = "NO" ]; then
    echo "ERROR: No backup file found"
    echo "The original excel_parser.py was not backed up."
    echo ""
    echo "You can restore from git:"
    echo "  docker exec $CONTAINER_NAME git checkout deepdoc/parser/excel_parser.py"
    exit 1
fi

# Restore original file
echo "[1/2] Restoring original Excel parser..."
docker exec "$CONTAINER_NAME" cp \
    /ragflow/deepdoc/parser/backup/excel_parser.py.original \
    /ragflow/deepdoc/parser/excel_parser.py

# Verify restoration
echo "[2/2] Verifying restoration..."
VERIFY=$(docker exec "$CONTAINER_NAME" python3 -c "
from deepdoc.parser.excel_parser import RAGFlowExcelParser
# Check if it's the original (no GPU acceleration function)
if hasattr(RAGFlowExcelParser, 'is_gpu_accelerated'):
    print('WARNING: Still using cuDF version')
else:
    print('Original version restored successfully')
" 2>&1)

echo "$VERIFY"

echo ""
echo "=============================================="
echo "Rollback Complete!"
echo "=============================================="
echo ""
echo "NOTE: Restart RAGFlow services for changes to take effect:"
echo "  docker compose restart ragflow-server"

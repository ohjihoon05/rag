# RAPIDS cuDF Excel Parser Patch for RAGFlow

GPU-accelerated Excel parsing for RAGFlow using NVIDIA RAPIDS cuDF.

## Overview

This patch replaces RAGFlow's default Excel parser with a GPU-accelerated version using RAPIDS cuDF. On Linux systems with NVIDIA GPUs, this can provide **10-150x speedup** for large Excel file processing.

### How It Works

- **Linux with NVIDIA GPU**: Uses `cudf.pandas` mode for transparent GPU acceleration
- **Windows/CPU Fallback**: Falls back to standard pandas (identical functionality)

```
┌─────────────────────────────────────────────────────────┐
│                  excel_parser_cudf.py                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  import check:                                          │
│  ├─ Linux + cuDF installed → GPU acceleration ON       │
│  └─ Windows / no cuDF     → CPU fallback (pandas)      │
│                                                         │
│  Result: Same API, same output, different speed         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Requirements

### Linux (Production - GPU Acceleration)
- NVIDIA GPU (Compute Capability 7.0+)
- CUDA 11.x or 12.x
- Docker with nvidia-container-toolkit
- RAGFlow Docker container running

### Windows (Testing - CPU Only)
- Python 3.10+
- pandas, openpyxl installed
- RAGFlow source code

## Quick Start

### 1. Test on Windows (CPU)

```powershell
# Navigate to patches directory
cd patches/rapids-cudf

# Run test script
python scripts/test_parser_windows.py

# Or test with your own Excel file
python scripts/test_parser_windows.py path/to/your/file.xlsx
```

Expected output:
```
===================================
ALL TESTS PASSED!
===================================
The cuDF parser produces identical results to the original.
Safe to deploy to Linux for GPU acceleration.
```

### 2. Deploy to Linux (GPU)

```bash
# Clone/copy this repository to your Linux server
git clone <your-repo> ragflow
cd ragflow

# Make sure RAGFlow is running
docker compose up -d

# Run the installation script
chmod +x patches/rapids-cudf/scripts/install_rapids.sh
./patches/rapids-cudf/scripts/install_rapids.sh

# Restart RAGFlow
docker compose restart ragflow-server
```

### 3. Verify GPU Acceleration

```bash
docker exec ragflow-server python3 -c "
from deepdoc.parser.excel_parser import get_acceleration_status
import json
print(json.dumps(get_acceleration_status(), indent=2))
"
```

Expected output:
```json
{
  "cudf_available": true,
  "gpu_accelerated": true,
  "platform": "Linux",
  "pandas_version": "2.2.3"
}
```

## File Structure

```
patches/rapids-cudf/
├── README.md                    # This file
├── excel_parser_cudf.py         # GPU-accelerated parser (replaces original)
├── scripts/
│   ├── install_rapids.sh        # Linux: Install cuDF + apply patch
│   ├── rollback_rapids.sh       # Linux: Restore original parser
│   └── test_parser_windows.py   # Windows: Test parser logic
└── backup/                      # Backup of original files (created during install)
```

## Detailed Usage

### Installation Script Options

```bash
# Default: targets 'ragflow-server' container
./scripts/install_rapids.sh

# Custom container name
./scripts/install_rapids.sh my-ragflow-container
```

### Rollback

```bash
# Restore original parser
./scripts/rollback_rapids.sh

# Verify rollback
docker exec ragflow-server python3 -c "
from deepdoc.parser.excel_parser import RAGFlowExcelParser
print('GPU method exists:', hasattr(RAGFlowExcelParser, 'is_gpu_accelerated'))
"
# Should print: GPU method exists: False
```

### Manual Installation (Alternative)

If you prefer manual installation:

```bash
# 1. Install cuDF in container
docker exec ragflow-server pip install cudf-cu12 \
    --extra-index-url=https://pypi.nvidia.com

# 2. Backup original parser
docker exec ragflow-server cp \
    /ragflow/deepdoc/parser/excel_parser.py \
    /ragflow/deepdoc/parser/excel_parser.py.backup

# 3. Copy new parser
docker cp excel_parser_cudf.py \
    ragflow-server:/ragflow/deepdoc/parser/excel_parser.py

# 4. Restart
docker compose restart ragflow-server
```

## Performance Comparison

Based on testing with Korean sales report Excel files (6000 rows, 10 columns):

| Operation | CPU (pandas) | GPU (cuDF) | Speedup |
|-----------|--------------|------------|---------|
| CSV Read | ~2.5s | ~0.1s | 25x |
| DataFrame Operations | ~1.0s | ~0.05s | 20x |
| Overall Parsing | ~135s | ~15s | 9x |

*Note: Actual speedup depends on file size, GPU model, and operation type.*

## Troubleshooting

### cuDF Installation Failed

```bash
# Check CUDA version
docker exec ragflow-server nvcc --version

# For CUDA 11.x, use different package
docker exec ragflow-server pip install cudf-cu11 \
    --extra-index-url=https://pypi.nvidia.com
```

### GPU Not Detected

```bash
# Check if GPU is visible in container
docker exec ragflow-server nvidia-smi

# If not visible, ensure docker-compose.yml has GPU config:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

### Parser Errors After Patch

```bash
# Check logs
docker logs ragflow-server 2>&1 | grep -i "excel\|cudf\|error"

# Rollback to original
./scripts/rollback_rapids.sh

# Restart
docker compose restart ragflow-server
```

## API Reference

The patched parser maintains full API compatibility with the original:

```python
from deepdoc.parser.excel_parser import RAGFlowExcelParser, get_acceleration_status

# Check acceleration status
status = get_acceleration_status()
# Returns: {'cudf_available': bool, 'gpu_accelerated': bool, 'platform': str, 'pandas_version': str}

# Create parser instance
parser = RAGFlowExcelParser()

# Check if GPU is active
parser.is_gpu_accelerated()  # Returns: bool

# Parse Excel file (returns list of row strings)
with open('file.xlsx', 'rb') as f:
    rows = parser(f.read())

# Generate HTML chunks
with open('file.xlsx', 'rb') as f:
    html_chunks = parser.html(f.read())

# Get row count
row_count = RAGFlowExcelParser.row_number('file.xlsx', binary_content)
```

## Known Limitations

1. **Linux Only for GPU**: RAPIDS cuDF only supports Linux. Windows always uses CPU.
2. **openpyxl Not Accelerated**: The `load_workbook` function from openpyxl is CPU-only. GPU acceleration only helps with pandas DataFrame operations.
3. **Memory Usage**: GPU acceleration requires additional VRAM (~1-2GB for typical workloads).

## License

Same as RAGFlow - Apache License 2.0

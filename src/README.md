# Source Code Directory Structure

This directory contains the restructured, production-ready source code for the Market Prediction project.

## 📂 Directory Overview

```
src/
├── data/               # Data collection and conversion
│   ├── collector.py    # WebSocket data collector from Coinbase
│   └── converters/     # Format conversion utilities
│       ├── jsonl_to_parquet.py   # GPU-accelerated JSONL → Parquet
│       └── csv_to_parquet.py     # CSV → Parquet utility
│
├── preprocessing/      # Data preprocessing (future)
│   ├── orderbook_builder.py     # TODO: Stage 2
│   └── feature_engineering.py   # TODO: Stage 3
│
├── models/            # Machine learning models (future)
│   ├── trainers/      # TODO: Training scripts
│   └── predictors/    # TODO: Prediction pipelines
│
└── utils/             # Shared utilities
    ├── gpu_memory.py      # GPU memory monitoring
    ├── parquet_utils.py   # Parquet I/O helpers
    └── __init__.py
```

## 🔧 Module Descriptions

### `data/collector.py`
**Purpose:** Real-time data collection from Coinbase WebSocket API

**Key Features:**
- Subscribes to Level 2 orderbook and ticker channels
- Buffers events in memory with periodic disk flushes
- Automatic daily file rotation
- Handles reconnections gracefully

**Usage:**
```python
from src.data.collector import CryptoDataCollector

collector = CryptoDataCollector(output_dir="crypto_data_jsonl")
# Runs continuously with auto-restart wrapper
```

**Wrapper Script:** `scripts/run_collector_24x7.py`

---

### `data/converters/jsonl_to_parquet.py`
**Purpose:** Convert raw JSONL WebSocket data to Parquet format (GPU-accelerated)

**Key Features:**
- GPU-accelerated processing with cuDF
- Handles nested JSON structure from WebSocket feed
- Batch processing (10M rows/chunk) to avoid GPU OOM
- Optional CSV export for Power BI integration
- Date-based partitioning for efficient querying

**Usage:**
```bash
# Basic conversion (skip latest file for safety)
python src/data/converters/jsonl_to_parquet.py

# Include all files
python src/data/converters/jsonl_to_parquet.py --include-latest

# Also export CSV for Power BI
python src/data/converters/jsonl_to_parquet.py --write-csv

# Validate existing Parquet files
python src/data/converters/jsonl_to_parquet.py --validate
```

**Performance:** ~200M rows in 10-15 minutes on NVIDIA DGX-A100

---

### `data/converters/csv_to_parquet.py`
**Purpose:** One-time conversion utility for existing CSV data

**Usage:**
```bash
python src/data/converters/csv_to_parquet.py
```

---

### `utils/gpu_memory.py`
**Purpose:** GPU memory monitoring and management

**Key Classes:**
- `GPUMemoryMonitor`: Context manager for tracking GPU memory usage
- `print_gpu_info()`: Display GPU device information

**Usage:**
```python
from src.utils.gpu_memory import GPUMemoryMonitor, print_gpu_info

print_gpu_info()

with GPUMemoryMonitor("conversion"):
    # GPU operations here
    df = cudf.read_parquet(...)
```

---

### `utils/parquet_utils.py`
**Purpose:** Parquet I/O helpers and metadata management

**Key Classes:**
- `ParquetManager`: Unified interface for reading/writing Parquet files
- `csv_to_parquet_batch()`: Batch conversion helper

---

## 🔗 Dependencies

### GPU Processing (DGX-A100)
```bash
pip install cudf-cu12 cupy-cuda12x rapids-dask-dependency
```

### Data Collection (Any System)
```bash
pip install websocket-client
```

### Configuration
All paths and settings are centralized in `config/gpu_config.py`

---

## 🚀 Quick Start

### 1. Collect Data (24/7)
```bash
cd scripts
python run_collector_24x7.py
```

### 2. Convert to Parquet (GPU)
```bash
python src/data/converters/jsonl_to_parquet.py --write-csv
```

### 3. Run Full Pipeline (Future)
```bash
cd scripts
python run_full_pipeline.py
```

---

## 📝 Import Guidelines

Always import from project root:

```python
# Correct
from config.gpu_config import JSONL_INPUT_DIR
from src.data.collector import CryptoDataCollector
from src.utils.gpu_memory import GPUMemoryMonitor

# Incorrect (relative imports)
from ..config import JSONL_INPUT_DIR  # Don't do this
```

Add project root to path if needed:
```python
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

---

## 🧪 Testing

Run structure validation:
```bash
python scripts/testing/test_structure.py
```

Expected output:
```
🎉 All tests passed! Project structure is valid.
```

---

## 📦 Migration Notes

This structure was created on **2025-11-22** (v0.1.0) as part of a major project cleanup.

**Key Changes:**
- Moved from flat structure to organized packages
- Centralized configuration in `config/`
- Archived 11 redundant docs and 4 duplicate scripts
- Updated all import paths

**See:** `_archive_old_structure/MIGRATION_LOG.md` for complete migration details

**Original files preserved in:**
- `gpu/` - Legacy GPU scripts (kept for backward compatibility)
- `data_pipeline/` - Legacy pipeline scripts (to be migrated)

---

## 🔮 Roadmap

### Immediate (v0.1.x)
- ✅ Stage 0: Data collection (collector.py)
- ✅ Stage 1: JSONL → Parquet conversion
- ⏳ Stage 2: Orderbook reconstruction
- ⏳ Stage 3: Feature engineering

### Short-term (v0.2.x)
- ⏳ Stage 4: Model training
- ⏳ Prediction pipeline
- Power BI dashboard integration

### Long-term (v0.3.x)
- Real-time prediction API
- Multi-asset support
- Automated retraining

---

**Last Updated:** 2025-11-22  
**Version:** 0.1.0

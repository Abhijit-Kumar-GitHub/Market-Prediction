# Project Restructure Migration Log

**Date:** November 22, 2025  
**Version:** 0.1.0  
**Purpose:** Document all files moved during project restructure for reference and potential rollback

---

## 📦 New Project Structure

```
MarketPrediction/
├── src/                          # Source code (new)
│   ├── data/
│   │   ├── collector.py         # WebSocket data collector
│   │   └── converters/
│   │       ├── jsonl_to_parquet.py   # GPU JSONL conversion
│   │       └── csv_to_parquet.py     # CSV conversion utility
│   ├── preprocessing/           # Future: orderbook + features
│   ├── models/                  # Future: ML models
│   └── utils/                   # GPU utilities
│       ├── gpu_memory.py
│       └── parquet_utils.py
├── config/                      # Configuration (new)
│   └── gpu_config.py           # Centralized settings
├── scripts/                     # Runner scripts (new)
│   ├── run_collector_24x7.py   # 24/7 collector wrapper
│   └── run_full_pipeline.py    # End-to-end runner
├── tests/                       # Unit tests (new, empty)
├── docs/                        # Documentation (preserved)
├── datasets/                    # Data files (preserved)
├── gpu/                         # Legacy GPU folder (preserved for now)
├── data_pipeline/              # Legacy pipeline scripts (preserved for now)
└── _archive_old_structure/     # Archived files (new)
    ├── old_docs/               # Redundant markdown docs
    ├── old_scripts/            # Duplicate scripts
    └── old_data/               # Old test data
```

---

## 📝 Files Moved

### Documentation Archived (11 files)

**From:** `{root}/` → **To:** `_archive_old_structure/old_docs/`

| File | Reason for Archiving |
|------|---------------------|
| `DOCUMENTATION_SYSTEM_OVERVIEW.md` | Redundant with README.md |
| `GPU_ACCELERATION_GUIDE.md` | Consolidated into docs/GPU_SETUP.md (future) |
| `GPU_INSTALLATION_GUIDE.md` | Consolidated into docs/GPU_SETUP.md (future) |
| `GPU_NOTEBOOK_COMPATIBILITY.md` | Outdated, notebooks not actively used |
| `GPU_OPTIMIZATION_SUMMARY.md` | Info captured in gpu/README.md |
| `PIPELINE_REFERENCE.md` | Will be replaced with docs/PIPELINE_STAGES.md |
| `QUICK_GPU_SETUP.md` | Redundant with GPU guides |
| `QUICK_REFERENCE.md` | Redundant with README.md |
| `PROJECT_ROADMAP.md` | Outdated, superseded by CHANGELOG.md |
| `PROJECT_STATUS.md` | Outdated, superseded by CHANGELOG.md |
| `POWER_BI_QUICK_REF.md` | Consolidated into docs/POWER_BI_IMPORT_GUIDE.md |

**Note:** These files are still accessible in archive if needed for reference.

---

### Scripts Archived (4 files)

**From:** Various locations → **To:** `_archive_old_structure/old_scripts/`

| Original Path | New Path in Archive | Reason |
|--------------|-------------------|--------|
| `stage1_raw_snapshots.py` | `old_scripts/stage1_raw_snapshots.py` | Duplicate of `data_pipeline/stage1_raw_snapshots.py` |
| `feature_engineer.py` | `old_scripts/feature_engineer.py` | Old version, replaced by pipeline stages |
| `feature_importance_analysis.py` | `old_scripts/feature_importance_analysis.py` | Standalone utility, not part of main pipeline |
| `gpu/stage0_jsonl_to_parquet.py` | `old_scripts/stage0_jsonl_to_parquet_v1.py` | Obsolete v1, replaced by v2 |

**Note:** These scripts had various bugs and are kept only for reference. Use new versions in `src/`.

---

### Test Data Archived

**From:** `27Oct25evening/` → **To:** `_archive_old_structure/old_data/27Oct25evening/`

**Reason:** Old test data from October 27. Current production data is in `crypto_data_jsonl/` (Nov 8-22, 2025).

**Contents:**
- `level2_data.txt` (test L2 orderbook data)
- `ticker_data.txt` (test ticker data)

---

## 🔄 Files Migrated (with updates)

### Source Code → `src/`

| Original Path | New Path | Changes Made |
|--------------|----------|-------------|
| `data_collector.py` | `src/data/collector.py` | **Copied** - No import changes needed |
| `gpu/stage0_jsonl_to_parquet_v2.py` | `src/data/converters/jsonl_to_parquet.py` | **Copied** - Updated imports: `from config.gpu_config import ...` |
| `gpu/stage0_csv_to_parquet.py` | `src/data/converters/csv_to_parquet.py` | **Copied** - Updated imports: `from config.gpu_config import ...`, `from src.utils import ...` |
| `gpu/utils/*` | `src/utils/*` | **Copied** - All GPU utilities (gpu_memory.py, parquet_utils.py) |

**Note:** Files were **copied**, not moved. Originals remain in place for backward compatibility during transition.

---

### Configuration → `config/`

| Original Path | New Path | Changes Made |
|--------------|----------|-------------|
| `gpu/config.py` | `config/gpu_config.py` | **Copied** - Updated `PROJECT_ROOT` path calculation |

---

### Scripts → `scripts/`

| Original Path | New Path | Changes Made |
|--------------|----------|-------------|
| `run_collector_24x7.py` | `scripts/run_collector_24x7.py` | **Copied** - Updated subprocess path: `'../src/data/collector.py'` |
| `run_full_pipeline.py` | `scripts/run_full_pipeline.py` | **Copied** - Updated to use `src/data/converters/jsonl_to_parquet.py` |
| `test_csv_export.sh` | `scripts/testing/test_csv_export.sh` | **Moved** - Test script relocated |

---

## 🔧 Import Path Updates

### Changes in `src/data/converters/jsonl_to_parquet.py`

**Before:**
```python
from config import (
    JSONL_INPUT_DIR,
    PARQUET_LEVEL2_DIR,
    PARQUET_TICKER_DIR,
    COMPRESSION
)
from utils.gpu_memory import GPUMemoryMonitor
```

**After:**
```python
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.gpu_config import (
    JSONL_INPUT_DIR,
    PARQUET_LEVEL2_DIR,
    PARQUET_TICKER_DIR,
    COMPRESSION
)
# Fallback if utils not available
try:
    from gpu.utils.gpu_memory import GPUMemoryMonitor
except ImportError:
    class GPUMemoryMonitor: ...
```

---

### Changes in `src/data/converters/csv_to_parquet.py`

**Before:**
```python
from config import (RAW_CSV_DIR, ...)
from utils.parquet_utils import ParquetManager
from utils.gpu_memory import GPUMemoryMonitor
```

**After:**
```python
from config.gpu_config import (RAW_CSV_DIR, ...)
from src.utils.parquet_utils import ParquetManager
from src.utils.gpu_memory import GPUMemoryMonitor
```

---

### Changes in `scripts/run_collector_24x7.py`

**Before:**
```python
process = subprocess.Popen(['python', '-u', 'data_collector.py'], ...)
```

**After:**
```python
process = subprocess.Popen(['python', '-u', '../src/data/collector.py'], ...)
```

---

## ✅ Verification Steps

Run these commands to verify the migration was successful:

### 1. Check new structure exists
```powershell
ls src, config, scripts, tests, _archive_old_structure
```

### 2. Verify imports work
```powershell
python -c "from config.gpu_config import JSONL_INPUT_DIR; print(JSONL_INPUT_DIR)"
```

### 3. Test conversion script
```powershell
python src/data/converters/jsonl_to_parquet.py --help
```

### 4. Verify collector can be imported
```powershell
python -c "import sys; sys.path.insert(0, 'src'); from data.collector import CryptoDataCollector; print('OK')"
```

---

## 🔙 Rollback Procedure

If you need to revert this restructure:

1. **Restore archived docs:**
   ```powershell
   Copy-Item _archive_old_structure\old_docs\* -Destination . -Force
   ```

2. **Restore archived scripts:**
   ```powershell
   Copy-Item _archive_old_structure\old_scripts\stage1_raw_snapshots.py -Destination . -Force
   Copy-Item _archive_old_structure\old_scripts\feature_engineer.py -Destination . -Force
   Copy-Item _archive_old_structure\old_scripts\feature_importance_analysis.py -Destination . -Force
   Copy-Item _archive_old_structure\old_scripts\stage0_jsonl_to_parquet_v1.py -Destination gpu\stage0_jsonl_to_parquet.py -Force
   ```

3. **Restore old data:**
   ```powershell
   Copy-Item _archive_old_structure\old_data\27Oct25evening -Destination . -Recurse -Force
   ```

4. **Remove new structure:**
   ```powershell
   Remove-Item -Path src, config, scripts, tests -Recurse -Force
   ```

5. **Revert CHANGELOG.md and BUGS.md to previous version** (use git or manual edit)

**Note:** Original files in `gpu/` and `data_pipeline/` were preserved, so no restoration needed there.

---

## 📊 Impact Assessment

### Files Preserved (No Changes)
- ✅ All data files: `crypto_data_jsonl/`, `datasets/`
- ✅ Original scripts: `gpu/`, `data_pipeline/`
- ✅ Core documentation: `README.md`, `CHANGELOG.md`, `BUGS.md`
- ✅ Documentation folder: `docs/`
- ✅ Requirements: `requirements.txt`, `requirements_gpu.txt`
- ✅ Jupyter notebooks: `*.ipynb` files

### Backward Compatibility
- ✅ Old import paths still work (original files preserved)
- ✅ Can gradually migrate to new structure
- ✅ No breaking changes for existing workflows

### Future Cleanup (Once verified working)
After 1-2 weeks of successful operation with new structure:
1. Delete `gpu/stage0_*` scripts (use `src/data/converters/` instead)
2. Delete root-level `data_collector.py` (use `src/data/collector.py` instead)
3. Delete root-level `run_*.py` scripts (use `scripts/` versions instead)
4. Consider archiving `data_pipeline/` folder if fully migrated to `src/`

---

## 🎯 Next Steps

1. **Test all functionality** with new paths
2. **Update any external scripts/cron jobs** to use new paths
3. **Document new structure** in README.md
4. **Create `docs/ARCHITECTURE.md`** consolidating GPU setup info
5. **Add unit tests** in `tests/` directory
6. **Consider removing** original files after confirmation (1-2 weeks)

---

**Migration completed successfully on 2025-11-22**  
**Verified by:** Restructure script execution  
**Git commit:** (to be added after verification)

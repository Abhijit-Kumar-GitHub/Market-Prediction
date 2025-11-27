# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### To Do
- Complete orderbook reconstruction (Stage 2) with GPU acceleration
- Complete ML feature engineering (Stage 3) with GPU acceleration
- Train all supervised models (Stage 4)
- Complete technical report
- Create presentation slides

---

## [0.1.1] - 2025-11-26

### Added
- Added specific exception handling (FileNotFoundError, JSONDecodeError, etc.)
- Added error tracking and logging throughout conversion pipeline
- Added verify_paths.py in scripts/testing to test if all paths work.

### Changed
- updated CHANGELOG.md

### Fixed  
- corrected the pathways, where they still used old file structure's file system.
- fixed jsonl_to_parquet.py to completely work (resolved date time formatting error mismatch (cudf) and other simple fixes)

### Misc  
- 

---

## [0.1.0] - 2025-11-22

### Added - Major Project Restructure
- **New project structure**: Organized code into `src/`, `config/`, `scripts/`, `tests/` directories
- **src/data/**: Data collection and conversion modules
  - `collector.py` - WebSocket data collector (formerly `data_collector.py`)
  - `converters/jsonl_to_parquet.py` - GPU conversion script (formerly `gpu/stage0_jsonl_to_parquet_v2.py`)
  - `converters/csv_to_parquet.py` - CSV to Parquet utility
- **src/utils/**: Shared GPU utilities (gpu_memory, parquet_utils)
- **config/**: Centralized configuration
  - `gpu_config.py` - All pipeline settings in one place (formerly `gpu/config.py`)
- **scripts/**: Runner scripts
  - `run_collector_24x7.py` - 24/7 collector wrapper
  - `run_full_pipeline.py` - End-to-end pipeline runner
- **Archive structure**: `_archive_old_structure/` for legacy files
  - `old_docs/` - 11 redundant markdown docs archived
  - `old_scripts/` - 4 duplicate scripts archived
  - `old_data/` - Old test data archived

### Changed
- Updated all import paths to use new structure
- Fixed import statements in conversion scripts to reference `config.gpu_config`
- Updated runner scripts to point to new file locations
- Consolidated GPU utilities under `src/utils/`

### Removed
- Archived 11 redundant documentation files from root:
  - DOCUMENTATION_SYSTEM_OVERVIEW.md, GPU_ACCELERATION_GUIDE.md, GPU_INSTALLATION_GUIDE.md
  - GPU_NOTEBOOK_COMPATIBILITY.md, GPU_OPTIMIZATION_SUMMARY.md, PIPELINE_REFERENCE.md
  - QUICK_GPU_SETUP.md, QUICK_REFERENCE.md, PROJECT_ROADMAP.md, PROJECT_STATUS.md
  - POWER_BI_QUICK_REF.md
- Archived duplicate scripts:
  - `stage1_raw_snapshots.py`, `feature_engineer.py`, `feature_importance_analysis.py` (root)
  - `gpu/stage0_jsonl_to_parquet.py` (v1, obsolete)
- Archived old test data: `27Oct25evening/` folder

### Misc
- This restructure addresses DEBT-001 (hard-coded paths) by centralizing configuration
- Improves code maintainability and professional appearance for portfolio/CV
- All existing functionality preserved, just reorganized

---

## [0.0.4] - 2025-11-08

### Added
- 

### Changed
- Made the run_collector_24x7.py automatically restart unless it fails consecutively for 8 times, even if websocket disconnects or it closes normally not just crashing
- Optimized buffer flushing mechanism again to display from run_collector_24x7.py  
- Refined the docs and customized it to suit my project from the initial template

### Fixed  
- websocket disconnect causing data collection to stop 

### Misc  
- Gotten access to Nvidia GDX 1000 Xenon server through LPU allowing me to run the my scripts non stop and collect data from it. 

---

## [0.0.3] - 2025-11-02

### Added
- Feature engineering pipeline (`feature_engineer.py`)
- Order book snapshot creation
- 25 feature extraction functions
- Merge with ticker data for targets
- Documentation suite (README, technical report template, presentation outline)
- Project roadmap and timeline

### Changed
- Improved error handling in data collector
- Optimized buffer flushing mechanism

### Fixed
- None yet

---

## [0.0.2] - 2025-10-28

### Added
- 24/7 data collection wrapper (`run_collector_24x7.py`)
- Auto-restart on failure
- Daily file rotation based on date
- Collection statistics tracking

### Changed
- Buffer size increased to 1000 records
- Flush interval changed to 30 seconds

### Fixed
- Memory leak in order book reconstruction

---

## [0.0.1] - 2025-10-27

### Added
- Initial data collector (`data_collector.py`)
- WebSocket connection to Coinbase
- Level 2 and ticker channel subscriptions
- JSONL file output format
- Basic statistics logging

---

## Version History
✅ Complete
🟡 In Progress
🔴 Planned

| Version | Date       | Description                          | Status                                 |
|---------|------------|--------------------------------------|----------------------------------------|
| 0.0.1   | 2025-10-25 | Initial data collector               | ✅ Complete                             
 |
| 0.0.4   | 2025-11-08 | 24/7 collection system               | ✅ Complete(14 days done on 2005-11-21) |
| 0.1.0   | 2025-11-22 | Complete project restructuring       | ✅ Complete                                    |
| 0.1.0   | 2025-11-22 | Data Exploration and Feature engineering                  | 🟡 In Progress                         |
| 0.4.0   | TBD        | Unsupervised learning                | 🔴 Planned                             |
| 0.5.0   | TBD        | Supervised learning (regression)     | 🔴 Planned                             |
| 0.6.0   | TBD        | Supervised learning (classification) | 🔴 Planned                             |
| 0.7.0   | TBD        | Model comparison & evaluation        | 🔴 Planned                             |
| 1.0.0   | TBD        | Complete documentation & publication | 🔴 Planned                             |

---

## Semantic Versioning Rules

This project follows semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** (1.0.0): Project complete and published
- **MINOR** (0.X.0): New major feature or phase complete
  - 0.1.0: Data collection
  - 0.2.0: Feature engineering
  - 0.3.0: Unsupervised learning
  - 0.4.0: Supervised regression
  - 0.5.0: Supervised classification
  - 0.6.0: Model comparison
  - 0.7.0: Documentation complete
- **PATCH** (0.0.X): Bug fixes, minor improvements

---

## How to Update This File

When making changes:

1. Add changes under `[Unreleased]` section
2. Use categories: Added, Changed, Deprecated, Removed, Fixed, Security
3. When releasing a version:
   - Move unreleased changes to new version section
   - Add version number and date
   - Update version history table

Example:
```markdown
## [Unreleased]

### Added
- New feature X

### Fixed
- Bug in Y

---

## [0.4.0] - 2025-11-15

### Added
- K-Means clustering implementation
- Hierarchical clustering
- Cluster visualization
```

---

## Links

- [Project Repository](https://github.com/yourusername/MarketPrediction)
- [Project Roadmap](PROJECT_ROADMAP.md)

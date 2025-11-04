# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### To Do
- Complete 14-day data collection
- Train all supervised models
- Complete technical report
- Create presentation slides

---

## [0.3.0] - 2025-11-02

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

## [0.2.0] - 2025-10-28

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
- File not found error on first run

---

## [0.1.0] - 2025-10-27

### Added
- Initial data collector (`data_collector.py`)
- WebSocket connection to Coinbase
- Level 2 and ticker channel subscriptions
- JSONL file output format
- Basic statistics logging

---

## Version History

| Version | Date | Description | Status |
|---------|------|-------------|--------|
| 0.1.0 | Oct 27, 2025 | Initial data collector | ✅ Complete |
| 0.2.0 | Oct 28, 2025 | 24/7 collection system | ✅ Complete |
| 0.3.0 | Nov 02, 2025 | Feature engineering | 🟡 In Progress |
| 0.4.0 | TBD | Unsupervised learning | 🔴 Planned |
| 0.5.0 | TBD | Supervised learning (regression) | 🔴 Planned |
| 0.6.0 | TBD | Supervised learning (classification) | 🔴 Planned |
| 0.7.0 | TBD | Model comparison & evaluation | 🔴 Planned |
| 1.0.0 | TBD | Complete documentation & publication | 🔴 Planned |

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
- [Issue Tracker](https://github.com/yourusername/MarketPrediction/issues)
- [Project Roadmap](PROJECT_ROADMAP.md)

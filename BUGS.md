# Bug Tracking & Issue Management

Someday soon i'll be setting this up on GitHub Issues  
🟡 Acknowledged  
🟢 Resolved (v0.0.2)  

---

## 🐛 Bugs


### [BUG-001] Order book reconstruction memory leak
**Status:** 🟢 Resolved (v0.0.2)  
**Priority:** High  
**Reported:** 2025-10-28  
**Resolved:** 2025-10-28

**Description:**
Memory usage grows unbounded during long data collection runs

**Root Cause:**
Order book dictionary not clearing old price levels

**Solution:**
Added logic to remove price levels when quantity = 0

---

### [BUG-002] Memory explosion due lotta snapshots
**Status:** 🟢 Resolved (v0.0.4)  
**Priority:** High  
**Reported:** 2025-11-07  
**Resolved:** 2025-11-08

**Description:**
After running the feature_engineering.py, the terminal freezes and becomes unresponsive and needs to be stopped via keyboard interrupt.

**Root Cause:**
in function parse_level2(), i am creating a snapshot for every single update event, which now i see is millions of snapshots. this is causing:
   - memory explosion as its storing every tiny order book change.
   - freezing/slowing of the system due to processing said snapshots. 

**Solution:**
Created sample snapshots at regular intervals instead of capturing every update. Set to 10 sec intervals - it worked!

---

### [BUG-003] Websocket Reconnection Data Loss
**Status:** 🟢 Resolved (v0.0.3)  
**Priority:** High  
**Reported:** 2025-11-13  
**Resolved:** 2025-11-13

**Description:**
When websocket disconnects and reconnects, Coinbase sends a full snapshot followed by updates. Previous code had logic that skipped creating output rows for subsequent snapshots (after the first one), causing **silent data gaps** during reconnections.

**Root Cause:**
Used `initial_snapshot_done` set to track which products had received their first snapshot. On reconnection, when a new snapshot arrived:
- Orderbook WAS correctly cleared and rebuilt
- But output row was NOT written (because product was already in `initial_snapshot_done`)
- Result: Missing snapshot rows in output CSV, creating timeline gaps

**Solution:**
Removed `initial_snapshot_done` tracking completely. Now ALWAYS process snapshots and create output rows, whether it's initial connection or reconnection. This ensures:
1. Orderbook is cleared and rebuilt (removes stale state)
2. Output row is created (no gaps in timeline)
3. Reconnections are handled transparently

**Files Modified:**
- `data_pipeline/stage2_orderbook_builder.py` (CPU version)
- `data_pipeline/stage2_orderbook_builder_GPU.py` (GPU version)

**Testing:**
Verified by intentionally disconnecting/reconnecting websocket and checking for continuous snapshot output with no timestamp gaps. Event type transitions (update → snapshot) indicate reconnections are being handled.

---

### [BUG-004] Sequence-based validation fails with collection restarts
**Status:** 🟢 Resolved (v0.1.2)  
**Priority:** High  
**Reported:** 2025-11-27  
**Resolved:** 2025-11-29

**Description:**
Data quality validation using sequence number completeness produced false positives, showing massive data gaps (50%+ missing) when actual data was complete. Cross-partition sequence linking was impossible.

**Root Cause:**
Collection restarts (4-5 per day) reset sequence numbers to 1, causing:
- Overlapping sequence ranges within same partition (Session 1: seq 1→500k, Session 2: seq 1→800k)
- Cannot distinguish between "missing data" and "session boundary"
- Sequence-based completeness calculation fundamentally broken for multi-session datasets

**Example:**
```
Same day partition contains:
Session 1: seq 1 → 500,000 (morning)
Session 2: seq 1 → 800,000 (afternoon - sequences restart!)
Session 3: seq 1 → 300,000 (evening - another restart!)

Sequence validation sees: max(800k) - min(1) + 1 = 800,001 expected
Actual unique sequences: ~1.6M (across all sessions)
False conclusion: 50% data loss (completely wrong!)
```

**Solution:**
Shifted to **temporal coverage validation** instead of sequence-based:
1. **Time-based gaps**: Flag periods >5 min with no updates (real data loss)
2. **Update rate**: Verify orderbook updates at expected frequency
3. **Session detection**: Identify restarts by sequence resets (negative diff)
4. **Coverage %**: (Time with data / Total time span) × 100

**Results After Fix:**
- Mean temporal coverage: **99.63%** across all 32 partitions
- Correctly identifies 5.1 sessions per day on average
- No false positives for data gaps
- Validation approach now production-ready

**Files Modified:**
- `notebooks/01_data_quality_validation.ipynb` (Cells 14-17)

**Key Insight:**
For streaming data with connection management, **time-based validation is the only reliable approach**. Sequence numbers are session-local, not globally continuous.

---

## ⚠️ Known Issues

### [ISSUE-001] WebSocket connection occasionally drops
**Status:** 🟢 Resolved (v0.0.2)  
**Priority:** Medium   
**Workaround:** Auto-restart script handles this

**Description:**
Coinbase WebSocket disconnects randomly every 6-12 hours

**Workaround:**
`run_collector_24x7.py` automatically restarts on disconnect

**Long-term Fix:**
Fixed it by ensuring thats restarts are not just for the crashed but websocket disconnects and normal closure of the script. it will keep on running until it fails consecutively for 8 times. Or maybe Dockerise it or host on virtual vm ... 
---

## 📋 Technical Debt

### [DEBT-001] Hard-coded file paths
**Status:** 🟢 Resolved (v0.1.0)  
**Priority:** Medium  

**Description:**
File paths were hard-coded in multiple places. Needed centralized config file.

**Resolution:**
Created `config/gpu_config.py` with centralized configuration using pathlib. All paths, GPU settings, and pipeline parameters now in one location. Updated all scripts to import from `config.gpu_config`.

**Files Updated:**
- `src/data/converters/jsonl_to_parquet.py`
- `src/data/converters/csv_to_parquet.py`
- All future pipeline stages will use centralized config

---

### [DEBT-003] Project structure chaos
**Status:** 🟢 Resolved (v0.1.0)  
**Priority:** High  

**Description:**
Project had grown organically with 11+ markdown docs at root level, duplicate scripts in multiple locations, and no clear organization. Made it hard to navigate and unprofessional for portfolio/CV.

**Resolution:**
Complete project restructure:
- Created proper Python package structure: `src/`, `config/`, `scripts/`, `tests/`
- Archived 11 redundant docs to `_archive_old_structure/old_docs/`
- Archived 4 duplicate scripts to `_archive_old_structure/old_scripts/`
- Moved working code to appropriate locations
- Updated all import paths
- Created `__init__.py` files for proper packages

**Files Archived:**
- Docs: DOCUMENTATION_SYSTEM_OVERVIEW.md, GPU_*.md, QUICK_*.md, PROJECT_*.md, POWER_BI_QUICK_REF.md
- Scripts: stage1_raw_snapshots.py, feature_engineer.py, feature_importance_analysis.py, gpu/stage0_jsonl_to_parquet.py (v1)
- Data: 27Oct25evening/ (old test data)

---

### [DEBT-002] No unit tests
**Priority:** High  


**Description:**
Critical functions lack unit tests

**Needs Tests:**
- Feature engineering functions
- Order book reconstruction
- Data validation

---

## 🔮 Future Enhancements

### [FEATURE-001] Real-time prediction API
**Priority:** Low (post-MVP)  

**Description:**
Flask/FastAPI endpoint for real-time predictions

**Requirements:**
- Load trained model
- Accept order book snapshot
- Return prediction + confidence

---

### [FEATURE-002] Multi-asset support
**Priority:** Medium  

**Description:**
Support multiple cryptocurrencies instead of just BTC/ETH

**Changes Needed:**
- Configurable product list
- Separate features per asset
- Cross-asset correlation features

---

### [FEATURE-003] Taking realtime data and updating the models periodically automatically
**Priority:** Low (post MVP)  

**Description:**
Allow realtime updation of model and correct identification of current trends for currect prediction  

**Changes Needed:**  
Still doing research regarding that

---

## 📊 Issue Statistics

| Category | Open  | In Progress | Resolved |
|----------|-------|-------------|----------|
| Bugs | 0     | 0 | 4        |
| Issues | 0     | 0 | 1        |
| Technical Debt | 2     | 0 | 2        |
| Features | 3     | 0 | 0        |
| **Total** | **5** | **0** | **7**    |

---

## 🏷️ Issue Template

When adding a new issue, use this template:

```markdown
### [TYPE-XXX] Short description
**Status:** 🔴 Open / 🟡 In Progress / 🟢 Resolved  
**Priority:** High / Medium / Low  
**Reported:** YYYY-MM-DD  
**Assigned to:** Name

**Description:**
What is the problem?

**Root Cause:** (for bugs)
Why does this happen?

**Solution:** (for bugs)
How to fix?

**Steps to Reproduce:** (for bugs)
1. Step 1
2. Step 2
3. See error

**Resolution Checklist:**
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

**Related Files:**
- file1.py
- file2.py
```

---

*Last Updated: 2025-11-29*

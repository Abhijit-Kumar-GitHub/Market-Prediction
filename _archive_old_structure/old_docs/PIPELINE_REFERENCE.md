# 3-Stage Data Pipeline - Quick Reference

## Architecture Overview

```
JSONL (.txt)  →  Event Log CSV  →  Snapshots CSV  →  ML Features CSV
   Stage 1           Stage 2           Stage 3
```

---

## Stage 1: JSONL → Event Log CSV
**File:** `stage1_raw_snapshots.py`
**Input:** `crypto_data_jsonl/level2_*.txt`, `ticker_*.txt`
**Output:** `datasets/raw_csv/level2_*.csv`, `ticker_*.csv`

### What it does:
- Pure JSON-to-CSV conversion
- No aggregation, no feature engineering
- Just flattens JSON events to tabular format

### Event log format:
```csv
timestamp,event_type,product_id,side,price_level,new_quantity
2025-11-07T...,snapshot,BTC-USD,bid,100882.73,0.2267
2025-11-07T...,l2update,BTC-USD,offer,100882.74,0.0373
```

### Run:
```bash
python stage1_raw_snapshots.py
```

---

## Stage 2: Event Log → Order Book Snapshots
**File:** `stage2_orderbook_builder.py`
**Input:** `datasets/raw_csv/level2_*.csv`, `ticker_*.csv`
**Output:** `datasets/market_snapshots.csv`

### What it does:
- Maintains in-memory order book state per product
- Applies snapshot/l2update events row-by-row
- Samples order book state every N seconds (default: 10s)
- Merges ticker data by timestamp + product_id
- Outputs "wide" snapshot format

### Snapshot format:
```csv
timestamp,product_id,best_bid,best_ask,bid_volume_10,ask_volume_10,ticker_price,ticker_volume_24h,...
2025-11-07T...,BTC-USD,100882.73,100882.74,1.5,0.75,100882.74,9732.34,...
```

### Key parameters:
- `snapshot_interval_seconds=10` - How often to sample order book state

### Run:
```bash
python stage2_orderbook_builder.py
```

---

## Stage 3: Snapshots → ML Features
**File:** `stage3_ml_features.py`
**Input:** `datasets/market_snapshots.csv`
**Output:** `datasets/crypto_features.csv`

### What it does:
- Loads snapshots (wide format with best_bid, best_ask, etc.)
- Computes derived features (spread, mid_price, order_imbalance)
- **Time-based target creation** using `pd.merge_asof`
- Optional rolling/lag features
- Final dataset ready for ML

### Features computed:
- `mid_price` = (best_bid + best_ask) / 2
- `spread` = best_ask - best_bid
- `spread_pct` = spread / mid_price * 100
- `order_imbalance` = (bid_vol - ask_vol) / (bid_vol + ask_vol)
- `future_price` = mid_price at (timestamp + target_horizon)
- `price_change_pct` = (future_price - mid_price) / mid_price * 100
- `direction` = 'up' | 'down' | 'flat' based on threshold

### Key parameters:
- `target_horizon_seconds=60` - How far into future to predict
- `price_change_threshold_pct=0.1` - ±% for up/down/flat labels
- `include_rolling=False` - Add rolling/lag features (slower)

### Run:
```bash
python stage3_ml_features.py
```

---

## Critical Fixes Applied to Stage 3

### 1. **Use mid_price for targets (not ticker_price)**
- Ticker price can have jumps/noise
- Mid-price is more stable representation of market state
- Better for short-term predictions

### 2. **direction='forward' (not 'nearest')**
- Avoids look-ahead bias
- Gets price AT OR AFTER target time
- Never uses future information that wasn't available

### 3. **Configurable thresholds**
- Default: ±0.1% (10 basis points)
- Adjust based on asset volatility
- Too tight = mostly 'flat', too loose = no signal

### 4. **Divide-by-zero guards**
- Order imbalance calculation protected
- Returns 0 when bid_vol + ask_vol = 0

### 5. **Numeric coercion & validation**
- Force numeric types early
- Drop rows with missing critical data
- Better error messages

---

## Full Pipeline Usage

```bash
# Step 1: Convert JSONL to event logs
python stage1_raw_snapshots.py

# Step 2: Build order book snapshots (merges ticker data)
python stage2_orderbook_builder.py

# Step 3: Compute ML features and targets
python stage3_ml_features.py
```

---

## Expected Performance

### Stage 1 (JSONL → CSV):
- **Speed:** ~50k-100k lines/sec
- **Memory:** Minimal (streaming)
- **For 2.8GB / 890k lines:** ~10-20 seconds

### Stage 2 (Event Log → Snapshots):
- **Speed:** ~10k-50k events/sec
- **Memory:** Low (maintains only current book state)
- **For 20M events:** ~5-10 minutes
- **Output size:** Much smaller (10s sampling: ~8.6k snapshots/day per product)

### Stage 3 (Snapshots → Features):
- **Speed:** Vectorized pandas (very fast)
- **Memory:** Loads full snapshot CSV
- **For 100k snapshots:** < 1 minute

---

## Debugging Tips

### Check Stage 1 output:
```bash
head -20 datasets/raw_csv/level2_20251107.csv
wc -l datasets/raw_csv/*.csv
```

### Check Stage 2 output:
```bash
head -20 datasets/market_snapshots.csv
# Look for: no negative spreads, ticker_price populated
```

### Check Stage 3 output:
```bash
head -20 datasets/crypto_features.csv
# Verify: price_change_pct reasonable, direction distribution balanced
```

### Common issues:
- **Negative spreads in Stage 2:** Check if snapshot/l2update logic is correct
- **All 'flat' labels in Stage 3:** Threshold too wide, reduce to 0.05%
- **All 'up' or 'down' in Stage 3:** Threshold too tight, increase to 0.5%
- **Missing ticker_price:** Stage 2 ticker merge failed, check timestamp alignment

# GPU-Accelerated Crypto Market Prediction Pipeline

## 🚀 Overview

This folder contains a **GPU-first**, **Parquet-based** pipeline designed for processing 14-15 days of crypto market data (~700M+ events, 30GB+) efficiently on NVIDIA DGX-A100.

### Why GPU + Parquet?

| Aspect | CSV (Current) | Parquet (New) | Improvement |
|--------|---------------|---------------|-------------|
| **Compression** | 30GB | 3-6GB | **5-10x smaller** |
| **Load Time** | 30-60s | 3-5s | **10-20x faster** |
| **Memory** | 60-90GB | 10-20GB | **3-6x less RAM** |
| **Column Select** | Load all | Load only needed | **Instant filtering** |
| **Partitioning** | No | By date/product | **Skip irrelevant data** |
| **GPU Optimized** | No | Yes | **Native cuDF format** |

---

## 📁 Pipeline Architecture

```
gpu/
├── README.md                          # This file
├── config.py                          # Centralized configuration
├── stage0_csv_to_parquet.py          # Convert existing CSV → Parquet (one-time)
├── stage1_collect_to_parquet.py      # Real-time collection → Parquet
├── stage2_orderbook_gpu.py           # GPU-native orderbook reconstruction
├── stage3_features_gpu.py            # GPU-native feature engineering
├── stage4_ml_training_gpu.py         # GPU-native model training (XGBoost, LightGBM)
├── analysis_gpu.ipynb                # GPU-native exploration notebook
└── utils/
    ├── __init__.py
    ├── parquet_utils.py              # Parquet read/write helpers
    ├── gpu_memory.py                 # GPU memory management
    └── performance.py                # Benchmarking utilities
```

---

## 🎯 Pipeline Stages

### Stage 0: JSONL → Parquet Conversion
**Purpose:** Convert raw websocket data (JSONL .txt files) directly to Parquet format

```bash
# Default: Write Parquet only
python gpu/stage0_jsonl_to_parquet_v2.py

# Write both Parquet and CSV (for Power BI compatibility)
python gpu/stage0_jsonl_to_parquet_v2.py --write-csv

# Include latest file (risky if collector is running)
python gpu/stage0_jsonl_to_parquet_v2.py --include-latest
```

**Why skip CSV intermediate step?**
- ✅ **Faster:** No intermediate CSV step (2x faster)
- ✅ **Less disk:** Don't store both CSV and Parquet (save 30GB)
- ✅ **Cleaner:** Direct path from collection → analysis
- ✅ **Simpler:** One conversion script instead of two

**CSV Export Option (`--write-csv`):**
- For Power BI Desktop import (see [Power BI Import Guide](../docs/POWER_BI_IMPORT_GUIDE.md))
- UTF-8 encoded, partitioned by date and product
- ~2x larger than Parquet on disk
- Use only if Power BI Parquet import not supported

**Features:**
- Read JSONL directly with cuDF (GPU-accelerated JSON parsing)
- Partition by date and product (`/date=2025-11-07/product_id=BTC-USD/`)
- Compress with Snappy (fast) or ZSTD (best compression)
- Validate schema consistency
- Handle both level2_*.txt and ticker_*.txt files
- Memory-efficient chunking (10M rows per batch)

**Input:**
```
crypto_data_jsonl/
├── level2_20251027.txt    # Raw websocket data (JSONL format)
├── level2_20251028.txt
├── level2_20251107.txt
├── ticker_20251027.txt
├── ticker_20251028.txt
└── ticker_20251107.txt
```

**Output:**
```
datasets/parquet/
├── level2/
│   ├── date=2025-10-27/
│   │   ├── product=BTC-USD/
│   │   │   └── data.parquet
│   │   └── product=ETH-USD/
│   │       └── data.parquet
│   ├── date=2025-10-28/
│   └── date=2025-11-07/
└── ticker/
    ├── date=2025-10-27/
    │   └── data.parquet
    ├── date=2025-10-28/
    └── date=2025-11-07/
        └── data.parquet
```

---

### Stage 1: Real-Time Collection → Parquet
**Purpose:** Collect new data directly to Parquet (replace `run_collector_24x7.py`)

```python
python gpu/stage1_collect_to_parquet.py --products BTC-USD ETH-USD
```

**Features:**
- Stream directly to Parquet (no CSV intermediate)
- Auto-partition by date (daily rollover)
- GPU-accelerated validation
- Memory-efficient buffering (10K events → flush)

---

### Stage 2: GPU-Native Orderbook Reconstruction
**Purpose:** Build market snapshots from Parquet data

```python
python gpu/stage2_orderbook_gpu.py --start-date 2025-11-01 --end-date 2025-11-15
```

**Features:**
- **Lazy loading:** Process 15 days without loading all to RAM
- **Column pruning:** Only load needed columns (timestamp, product, side, price, qty)
- **Partitioning:** Filter by date before reading (skip 90% of data)
- **GPU orderbook:** Vectorized updates (no Python loops)
- **Streaming output:** Write Parquet incrementally (never run out of memory)

**Output:**
```
datasets/parquet/snapshots/
├── date=2025-11-07/
│   └── snapshots.parquet  # ~17K snapshots/day
└── date=2025-11-08/
    └── snapshots.parquet
```

---

### Stage 3: GPU-Native Feature Engineering
**Purpose:** Compute 60+ ML features on GPU

```python
python gpu/stage3_features_gpu.py --start-date 2025-11-01 --end-date 2025-11-15
```

**Features:**
- **cuDF rolling windows:** 30x faster than pandas
- **CuPy ufuncs:** GPU-accelerated RSI, MACD, Bollinger Bands
- **Lazy evaluation:** Only compute features when needed
- **Incremental output:** Process day-by-day to avoid OOM

**Output:**
```
datasets/parquet/features/
├── date=2025-11-07/
│   └── features.parquet  # ~17K rows × 60+ features
└── date=2025-11-08/
    └── features.parquet
```

---

### Stage 4: GPU-Native Model Training
**Purpose:** Train XGBoost/LightGBM models on GPU

```python
python gpu/stage4_ml_training_gpu.py --train-days 10 --val-days 2 --test-days 3
```

**Features:**
- **XGBoost GPU:** `tree_method='gpu_hist'` (50x faster)
- **LightGBM GPU:** `device='gpu'` (20x faster)
- **cuML models:** Random Forest, Ridge, Lasso on GPU
- **Lazy data loading:** Train on 15 days without loading all to RAM
- **GPU inference:** Predict 100x faster

---

## 🔧 Configuration

All settings in `config.py`:

```python
# Paths
PARQUET_DIR = "datasets/parquet"
RAW_CSV_DIR = "datasets/raw_csv"

# Partitioning
PARTITION_COLS = ['date', 'product_id']

# Compression
COMPRESSION = 'snappy'  # Options: 'snappy', 'gzip', 'zstd'

# GPU Memory
GPU_MEMORY_LIMIT = "80GB"  # For A100 (leave 20GB for overhead)

# Processing
CHUNK_SIZE = 10_000_000  # 10M rows per chunk
SNAPSHOT_INTERVAL_SEC = 10

# Features
ROLLING_WINDOWS = [5, 10, 20, 50, 100]  # For moving averages
```

---

## 📊 Performance Benchmarks (Expected)

### Stage 0: CSV → Parquet Conversion
- **Input:** 30GB CSV (14 days)
- **Output:** 3-6GB Parquet
- **Time:** 5-10 minutes (GPU-accelerated)
- **Compression:** 5-10x

### Stage 2: Orderbook Reconstruction (15 days)
- **Input:** 700M+ events (Parquet)
- **Output:** ~250K snapshots (Parquet)
- **Time:** 10-15 minutes (was: 5-7 hours on CPU)
- **Speedup:** 20-40x

### Stage 3: Feature Engineering (15 days)
- **Input:** 250K snapshots
- **Output:** 250K × 60 features
- **Time:** 3-5 minutes (was: 2-3 hours on CPU)
- **Speedup:** 30-40x

### Stage 4: Model Training (15 days)
- **Input:** 250K samples
- **Training Time:** 1-2 minutes (was: 20-30 min on CPU)
- **Speedup:** 10-20x

### Total Pipeline: 15 days of data
- **CSV Pipeline:** ~8 hours
- **Parquet + GPU:** ~20 minutes
- **Overall Speedup:** 24x

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
conda activate rapids-market
pip install pyarrow  # For Parquet support
```

### 2. Convert Existing Data (One-Time)
```bash
python gpu/stage0_csv_to_parquet.py
```

### 3. Run Full Pipeline
```bash
# Process 15 days
python gpu/stage2_orderbook_gpu.py --start-date 2025-11-01 --end-date 2025-11-15
python gpu/stage3_features_gpu.py --start-date 2025-11-01 --end-date 2025-11-15
python gpu/stage4_ml_training_gpu.py --train-days 10 --val-days 2 --test-days 3
```

### 4. Explore Data
```bash
jupyter lab gpu/analysis_gpu.ipynb
```

---

## 💡 Key Design Principles

### 1. **Lazy Loading (Never Load Everything)**
```python
# ❌ BAD: Load all 15 days (90GB in RAM)
df = cudf.read_parquet('datasets/parquet/level2/**/*.parquet')

# ✅ GOOD: Load one day at a time
for date in date_range:
    df = cudf.read_parquet(f'datasets/parquet/level2/date={date}/**/*.parquet')
    process(df)  # Max 6GB in RAM
```

### 2. **Column Pruning (Read Only What You Need)**
```python
# ❌ BAD: Load all columns (6GB)
df = cudf.read_parquet(file)

# ✅ GOOD: Load only needed columns (1GB)
df = cudf.read_parquet(file, columns=['timestamp', 'price_level', 'new_quantity'])
```

### 3. **Partitioning (Skip Irrelevant Data)**
```python
# ❌ BAD: Read all dates, filter after (10x slower)
df = cudf.read_parquet('datasets/parquet/level2/**/*.parquet')
df = df[df['date'] == '2025-11-07']

# ✅ GOOD: Use partition pruning (10x faster)
df = cudf.read_parquet('datasets/parquet/level2/date=2025-11-07/**/*.parquet')
```

### 4. **Incremental Processing (Streaming)**
```python
# ❌ BAD: Accumulate all results (OOM after 15 days)
results = []
for date in dates:
    result = process(date)
    results.append(result)  # 90GB accumulated!
all_results = cudf.concat(results)

# ✅ GOOD: Write incrementally
for date in dates:
    result = process(date)
    result.to_parquet(f'output/date={date}/data.parquet')  # Max 6GB at a time
```

### 5. **GPU Memory Management**
```python
# Monitor GPU memory
import cupy as cp
mempool = cp.get_default_memory_pool()
print(f"GPU Memory: {mempool.used_bytes() / 1024**3:.1f} GB / {mempool.total_bytes() / 1024**3:.1f} GB")

# Free memory after each chunk
del df
cp._default_memory_pool.free_all_blocks()
```

---

## 📈 Advantages Over CSV Pipeline

| Feature | CSV Pipeline | Parquet Pipeline | Benefit |
|---------|--------------|------------------|---------|
| **File Size** | 30GB | 3-6GB | Save disk space |
| **Load Time** | 30-60s | 3-5s | Start analysis faster |
| **Memory Usage** | 60-90GB | 10-20GB | Fit 15 days in GPU |
| **Column Select** | Load all | Select needed | 5-10x faster queries |
| **Partitioning** | Manual | Automatic | Skip 90% of data |
| **Compression** | None | Snappy/ZSTD | Transfer faster |
| **Schema** | Inferred | Stored | No type errors |
| **Metadata** | None | Stored | Instant statistics |
| **Append** | Rewrite file | Append partition | Incremental updates |
| **Query Speed** | Scan all | Predicate pushdown | 10-100x faster |

---

## 🎓 Interview Talking Points

### Technical Depth:
1. **"We use Parquet with GPU-optimized partitioning"**
   - Explain: Columnar format, predicate pushdown, partition pruning
   - Impact: Process 15 days (700M rows) in 20 minutes vs 8 hours

2. **"Lazy evaluation + incremental processing"**
   - Explain: Never load entire dataset, stream results to disk
   - Impact: Handle datasets larger than GPU memory (90GB → 20GB chunks)

3. **"GPU-native pipeline with cuDF/CuPy"**
   - Explain: No pandas conversions, vectorized orderbook updates
   - Impact: 20-40x speedup on data processing

4. **"XGBoost GPU training on 700M events"**
   - Explain: `tree_method='gpu_hist'`, lazy data loading
   - Impact: Train models 50x faster (30 min → 1 min)

### Business Value:
- **Research velocity:** Experiment 24x faster
- **Cost efficiency:** Process more data with same hardware
- **Scalability:** Easily extend to 30+ days
- **Production-ready:** Same code for research & deployment

---

## 📝 Next Steps

1. **Convert existing CSV to Parquet** (Stage 0)
2. **Validate Parquet loading** (test read speed)
3. **Build GPU orderbook pipeline** (Stage 2)
4. **Implement lazy feature engineering** (Stage 3)
5. **Train GPU models** (Stage 4)
6. **Benchmark everything** (prove 24x speedup)

---

## 🔗 References

- [RAPIDS cuDF Documentation](https://docs.rapids.ai/api/cudf/stable/)
- [Apache Parquet Format](https://parquet.apache.org/docs/)
- [XGBoost GPU Training](https://xgboost.readthedocs.io/en/latest/gpu/index.html)
- [Partition Pruning Explained](https://arrow.apache.org/docs/python/parquet.html#partitioned-datasets)

---

**Status:** Architecture designed, ready for implementation  
**Expected Timeline:** 2-3 days to build all stages  
**Expected Performance:** 24x faster than CSV pipeline

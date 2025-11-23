"""
GPU Pipeline Configuration

Centralized configuration for all GPU-accelerated pipeline stages.
All paths, parameters, and settings in one place.
"""

from pathlib import Path

# Export all configuration variables
__all__ = [
    # Paths
    'PROJECT_ROOT', 'DATA_DIR',
    'RAW_CSV_DIR', 'JSONL_INPUT_DIR',
    'PARQUET_DIR', 'PARQUET_LEVEL2_DIR', 'PARQUET_TICKER_DIR',
    'PARQUET_SNAPSHOTS_DIR', 'PARQUET_FEATURES_DIR',
    'MODELS_DIR', 'PREDICTIONS_DIR', 'LOGS_DIR', 'METRICS_DIR',
    # Parquet settings
    'COMPRESSION', 'LEVEL2_PARTITION_COLS', 'TICKER_PARTITION_COLS',
    'SNAPSHOT_PARTITION_COLS', 'FEATURE_PARTITION_COLS', 'ROW_GROUP_SIZE',
    # GPU settings
    'GPU_MEMORY_LIMIT_GB', 'GPU_DEVICE_ID',
    'ENABLE_GPU_MEMORY_POOL', 'MEMORY_POOL_RELEASE_THRESHOLD',
    # Processing settings
    'CHUNK_SIZE_ROWS', 'BUFFER_SIZE_EVENTS', 'PROCESS_DAYS_AT_ONCE', 'NUM_WORKERS',
    # Orderbook settings
    'SNAPSHOT_INTERVAL_SEC', 'ORDERBOOK_DEPTH_LEVELS',
    'ENABLE_OUTLIER_FILTER', 'OUTLIER_THRESHOLD_PCT',
]

# ============================================================================
# PATHS
# ============================================================================

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "datasets"

# Input paths (existing data)
RAW_CSV_DIR = DATA_DIR / "raw_csv"         # Legacy CSV files (if any)
JSONL_INPUT_DIR = PROJECT_ROOT / "crypto_data_jsonl"  # Raw JSONL websocket data (.txt files)

# Output paths (Parquet format)
PARQUET_DIR = DATA_DIR / "parquet"
PARQUET_LEVEL2_DIR = PARQUET_DIR / "level2"
PARQUET_TICKER_DIR = PARQUET_DIR / "ticker"
PARQUET_SNAPSHOTS_DIR = PARQUET_DIR / "snapshots"
PARQUET_FEATURES_DIR = PARQUET_DIR / "features"

# Model outputs
MODELS_DIR = PROJECT_ROOT / "models"
PREDICTIONS_DIR = DATA_DIR / "predictions"

# Logs and metrics
LOGS_DIR = PROJECT_ROOT / "logs"
METRICS_DIR = PROJECT_ROOT / "metrics"

# ============================================================================
# PARQUET SETTINGS
# ============================================================================

# Compression (trade-off: speed vs size)
# Options: 'snappy' (fast, 3-5x), 'gzip' (medium, 5-8x), 'zstd' (slow, 8-12x)
COMPRESSION = 'snappy'

# Partitioning columns (for predicate pushdown)
LEVEL2_PARTITION_COLS = ['date', 'product_id']  # e.g., date=2025-11-07/product=BTC-USD/
TICKER_PARTITION_COLS = ['date']
SNAPSHOT_PARTITION_COLS = ['date']
FEATURE_PARTITION_COLS = ['date']

# Row group size (larger = better compression, less parallelism)
ROW_GROUP_SIZE = 1_000_000  # 1M rows per row group

# ============================================================================
# GPU SETTINGS
# ============================================================================

# GPU memory limit (leave 20-30% for system overhead)
# A100 80GB → use 60GB max
GPU_MEMORY_LIMIT_GB = 60

# Device selection
GPU_DEVICE_ID = 0  # Which GPU to use (0-7 on DGX-A100)

# Memory pool settings
ENABLE_GPU_MEMORY_POOL = True
MEMORY_POOL_RELEASE_THRESHOLD = 0.8  # Release memory when 80% full

# ============================================================================
# PROCESSING SETTINGS
# ============================================================================

# Chunk sizes (how much data to process at once)
CHUNK_SIZE_ROWS = 10_000_000  # 10M rows per chunk
BUFFER_SIZE_EVENTS = 10_000   # Buffer 10K events before flushing to Parquet

# Date range processing
PROCESS_DAYS_AT_ONCE = 1  # Process 1 day at a time (prevents OOM)

# Parallelism
NUM_WORKERS = 4  # For multi-threaded operations

# ============================================================================
# ORDERBOOK SETTINGS (Stage 2)
# ============================================================================

# Snapshot interval
SNAPSHOT_INTERVAL_SEC = 10  # Create snapshot every 10 seconds

# Orderbook depth
ORDERBOOK_DEPTH_LEVELS = 10  # Track top 10 bids/asks

# Outlier filtering (EMA-based)
ENABLE_OUTLIER_FILTER = True
OUTLIER_THRESHOLD_PCT = 10  # Filter prices >10% from EMA mid-price
EMA_ALPHA = 0.05  # Smoothing factor for EMA

# Crossed book handling
SKIP_CROSSED_BOOKS = True  # Skip snapshots where bid >= ask

# Products to process
PRODUCTS = ['BTC-USD', 'ETH-USD']

# ============================================================================
# FEATURE ENGINEERING SETTINGS (Stage 3)
# ============================================================================

# Rolling window sizes (for moving averages, volatility, etc.)
ROLLING_WINDOWS = [5, 10, 20, 50, 100, 200]

# Technical indicators
ENABLE_TECHNICAL_INDICATORS = True
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2
STOCHASTIC_K = 14
STOCHASTIC_D = 3
ATR_PERIOD = 14

# Microstructure features
ENABLE_VPIN = True
VPIN_BUCKET_SIZE = 50  # Bucket size for volume-synchronized probability of informed trading

ENABLE_ORDER_IMBALANCE = True
IMBALANCE_DEPTH_LEVELS = 5  # Top 5 levels for imbalance calculation

# Lag features
LAG_PERIODS = [1, 2, 3, 5, 10]  # Create lagged features

# ============================================================================
# MODEL TRAINING SETTINGS (Stage 4)
# ============================================================================

# Train/Val/Test split
TRAIN_DAYS = 10
VAL_DAYS = 2
TEST_DAYS = 3

# Target variable
TARGET_HORIZON_SEC = 60  # Predict price movement 60 seconds ahead
TARGET_TYPE = 'returns'  # Options: 'returns', 'direction', 'volatility'

# XGBoost GPU settings
XGBOOST_PARAMS = {
    'tree_method': 'gpu_hist',  # GPU-accelerated training
    'gpu_id': GPU_DEVICE_ID,
    'max_depth': 8,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'reg:squarederror',
    'eval_metric': 'rmse',
    'early_stopping_rounds': 50
}

# LightGBM GPU settings
LIGHTGBM_PARAMS = {
    'device': 'gpu',
    'gpu_platform_id': 0,
    'gpu_device_id': GPU_DEVICE_ID,
    'max_depth': 8,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'regression',
    'metric': 'rmse',
    'early_stopping_rounds': 50,
    'verbose': -1
}

# Feature selection
ENABLE_FEATURE_SELECTION = True
FEATURE_IMPORTANCE_THRESHOLD = 0.001  # Drop features with <0.1% importance

# ============================================================================
# DATA COLLECTION SETTINGS (Stage 1)
# ============================================================================

# Websocket settings
WS_URL = "wss://ws-feed.exchange.coinbase.com"
RECONNECT_DELAY_SEC = 5
MAX_RECONNECT_ATTEMPTS = 10

# Channels to subscribe
SUBSCRIBE_CHANNELS = ['level2_batch', 'ticker_batch']

# Flush interval (how often to write buffer to Parquet)
FLUSH_INTERVAL_SEC = 60  # Flush every 60 seconds

# ============================================================================
# LOGGING AND MONITORING
# ============================================================================

# Logging level
LOG_LEVEL = 'INFO'  # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'

# Performance metrics
ENABLE_PERFORMANCE_LOGGING = True
LOG_GPU_MEMORY_EVERY_N_CHUNKS = 10  # Log GPU memory every 10 chunks

# Progress reporting
ENABLE_PROGRESS_BAR = True

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Schema validation
ENABLE_SCHEMA_VALIDATION = True

# Data quality checks
CHECK_FOR_NULLS = True
CHECK_FOR_DUPLICATES = True
CHECK_TIMESTAMP_MONOTONIC = True

# Expected schemas
LEVEL2_SCHEMA = {
    'timestamp': 'int64',
    'datetime': 'datetime64[ns]',
    'event_type': 'object',  # or 'type'
    'product_id': 'object',
    'side': 'object',
    'price_level': 'float64',
    'new_quantity': 'float64'
}

TICKER_SCHEMA = {
    'timestamp': 'int64',
    'datetime': 'datetime64[ns]',
    'product_id': 'object',
    'price': 'float64',
    'volume_24_h': 'float64',
    'high_24_h': 'float64',
    'low_24_h': 'float64',
    'best_bid': 'float64',
    'best_ask': 'float64'
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_directories():
    """Create all necessary directories if they don't exist."""
    dirs = [
        PARQUET_DIR,
        PARQUET_LEVEL2_DIR,
        PARQUET_TICKER_DIR,
        PARQUET_SNAPSHOTS_DIR,
        PARQUET_FEATURES_DIR,
        MODELS_DIR,
        PREDICTIONS_DIR,
        LOGS_DIR,
        METRICS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {len(dirs)} directories")


def get_date_partition_path(base_dir: Path, date: str, product: str = None) -> Path:
    """
    Get partition path for a given date and optionally product.
    
    Args:
        base_dir: Base directory (e.g., PARQUET_LEVEL2_DIR)
        date: Date string in YYYY-MM-DD format
        product: Optional product ID (e.g., 'BTC-USD')
    
    Returns:
        Path to partition directory
    
    Example:
        >>> get_date_partition_path(PARQUET_LEVEL2_DIR, '2025-11-07', 'BTC-USD')
        PosixPath('datasets/parquet/level2/date=2025-11-07/product=BTC-USD')
    """
    path = base_dir / f"date={date}"
    if product:
        path = path / f"product={product}"
    return path


def get_parquet_filters(start_date: str = None, end_date: str = None, 
                         product: str = None) -> list:
    """
    Create Parquet predicate pushdown filters.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        product: Product ID filter
    
    Returns:
        List of filter tuples for pyarrow
    
    Example:
        >>> get_parquet_filters('2025-11-01', '2025-11-15', 'BTC-USD')
        [('date', '>=', '2025-11-01'), ('date', '<=', '2025-11-15'), 
         ('product_id', '==', 'BTC-USD')]
    """
    filters = []
    
    if start_date:
        filters.append(('date', '>=', start_date))
    if end_date:
        filters.append(('date', '<=', end_date))
    if product:
        filters.append(('product_id', '==', product))
    
    return filters if filters else None


if __name__ == '__main__':
    # Test configuration
    print("=" * 80)
    print("GPU PIPELINE CONFIGURATION")
    print("=" * 80)
    
    print(f"\n📁 Paths:")
    print(f"  Raw CSV:  {RAW_CSV_DIR}")
    print(f"  Parquet:  {PARQUET_DIR}")
    print(f"  Models:   {MODELS_DIR}")
    
    print(f"\n🎮 GPU Settings:")
    print(f"  Device:   GPU {GPU_DEVICE_ID}")
    print(f"  Memory:   {GPU_MEMORY_LIMIT_GB} GB")
    
    print(f"\n⚙️  Processing:")
    print(f"  Chunk size:     {CHUNK_SIZE_ROWS:,} rows")
    print(f"  Snapshot freq:  {SNAPSHOT_INTERVAL_SEC}s")
    print(f"  Products:       {', '.join(PRODUCTS)}")
    
    print(f"\n📊 Features:")
    print(f"  Rolling windows:  {ROLLING_WINDOWS}")
    print(f"  Technical indicators: {ENABLE_TECHNICAL_INDICATORS}")
    print(f"  VPIN enabled:     {ENABLE_VPIN}")
    
    print(f"\n🤖 Model Training:")
    print(f"  Train/Val/Test:  {TRAIN_DAYS}/{VAL_DAYS}/{TEST_DAYS} days")
    print(f"  Target horizon:  {TARGET_HORIZON_SEC}s")
    
    print(f"\n✓ Creating directories...")
    create_directories()
    
    print(f"\n✓ Testing filter generation...")
    filters = get_parquet_filters('2025-11-01', '2025-11-15', 'BTC-USD')
    print(f"  Filters: {filters}")
    
    print("\n" + "=" * 80)
    print("✅ CONFIGURATION LOADED SUCCESSFULLY")
    print("=" * 80)

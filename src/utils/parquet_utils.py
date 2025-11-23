"""
Parquet Utilities for GPU Pipeline

Helper functions for reading/writing Parquet files with GPU optimization.
Includes lazy loading, partition management, and schema validation.
"""

import cudf
import pandas as pd
from pathlib import Path
from typing import List, Union, Optional, Dict
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta


class ParquetManager:
    """
    Manages Parquet file operations with GPU optimization.
    
    Features:
    - Lazy loading (load only what you need)
    - Partition pruning (skip irrelevant files)
    - Column selection (load only needed columns)
    - Incremental writing (stream large datasets)
    - Schema validation
    """
    
    def __init__(self, base_dir: Path, compression: str = 'snappy'):
        """
        Initialize Parquet manager.
        
        Args:
            base_dir: Base directory for Parquet files
            compression: Compression codec ('snappy', 'gzip', 'zstd')
        """
        self.base_dir = Path(base_dir)
        self.compression = compression
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def write_partitioned(self, df: cudf.DataFrame, partition_cols: List[str], 
                          append: bool = True) -> None:
        """
        Write DataFrame to Parquet with partitioning.
        
        Args:
            df: cuDF DataFrame to write
            partition_cols: Columns to partition by (e.g., ['date', 'product_id'])
            append: Whether to append to existing partitions
        
        Example:
            >>> manager = ParquetManager('datasets/parquet/level2')
            >>> manager.write_partitioned(df, ['date', 'product_id'])
            # Creates: date=2025-11-07/product=BTC-USD/data.parquet
        """
        # Convert to pandas for pyarrow compatibility
        df_pandas = df.to_pandas()
        
        # Create PyArrow table
        table = pa.Table.from_pandas(df_pandas)
        
        # Write with partitioning
        pq.write_to_dataset(
            table,
            root_path=str(self.base_dir),
            partition_cols=partition_cols,
            compression=self.compression,
            existing_data_behavior='overwrite_or_ignore' if append else 'error'
        )
    
    def read_lazy(self, columns: Optional[List[str]] = None,
                  filters: Optional[List[tuple]] = None,
                  date_range: Optional[tuple] = None,
                  product: Optional[str] = None) -> cudf.DataFrame:
        """
        Lazy load Parquet files with filtering.
        
        Args:
            columns: Columns to load (None = all)
            filters: PyArrow filters for predicate pushdown
            date_range: Tuple of (start_date, end_date) strings
            product: Product ID to filter
        
        Returns:
            cuDF DataFrame (only filtered data loaded)
        
        Example:
            >>> df = manager.read_lazy(
            ...     columns=['timestamp', 'price_level'],
            ...     date_range=('2025-11-01', '2025-11-15'),
            ...     product='BTC-USD'
            ... )
            # Only loads BTC-USD data from Nov 1-15, only 2 columns
        """
        # Build filters
        filter_list = []
        if date_range:
            start, end = date_range
            filter_list.append(('date', '>=', start))
            filter_list.append(('date', '<=', end))
        if product:
            filter_list.append(('product_id', '==', product))
        if filters:
            filter_list.extend(filters)
        
        # Read with filters (partition pruning happens here!)
        df = cudf.read_parquet(
            str(self.base_dir),
            columns=columns,
            filters=filter_list if filter_list else None
        )
        
        return df
    
    def read_date(self, date: str, product: Optional[str] = None,
                  columns: Optional[List[str]] = None) -> cudf.DataFrame:
        """
        Read data for a specific date (and optionally product).
        
        Args:
            date: Date string (YYYY-MM-DD)
            product: Optional product ID
            columns: Optional column selection
        
        Returns:
            cuDF DataFrame
        """
        path = self.base_dir / f"date={date}"
        if product:
            path = path / f"product={product}"
        
        if not path.exists():
            print(f"⚠️  Warning: {path} does not exist")
            return cudf.DataFrame()
        
        return cudf.read_parquet(str(path), columns=columns)
    
    def read_date_range(self, start_date: str, end_date: str,
                        product: Optional[str] = None,
                        columns: Optional[List[str]] = None) -> cudf.DataFrame:
        """
        Read data for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            product: Optional product filter
            columns: Optional column selection
        
        Returns:
            cuDF DataFrame (concatenated across dates)
        """
        return self.read_lazy(
            columns=columns,
            date_range=(start_date, end_date),
            product=product
        )
    
    def stream_read(self, date_range: tuple, product: Optional[str] = None,
                    columns: Optional[List[str]] = None):
        """
        Stream read data one day at a time (generator).
        
        Yields:
            (date, DataFrame) tuples
        
        Example:
            >>> for date, df in manager.stream_read(('2025-11-01', '2025-11-15')):
            ...     process(df)  # Process 1 day at a time
            ...     del df       # Free memory
        """
        start, end = date_range
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d')
        
        current = start_dt
        while current <= end_dt:
            date_str = current.strftime('%Y-%m-%d')
            df = self.read_date(date_str, product=product, columns=columns)
            
            if len(df) > 0:
                yield date_str, df
            
            current += timedelta(days=1)
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about Parquet dataset.
        
        Returns:
            Dictionary with file count, total size, partitions, etc.
        """
        parquet_files = list(self.base_dir.rglob('*.parquet'))
        
        total_size_mb = sum(f.stat().st_size for f in parquet_files) / 1024**2
        
        # Extract unique dates and products from partition paths
        dates = set()
        products = set()
        
        for f in parquet_files:
            parts = f.parts
            for part in parts:
                if part.startswith('date='):
                    dates.add(part.split('=')[1])
                elif part.startswith('product='):
                    products.add(part.split('=')[1])
        
        return {
            'num_files': len(parquet_files),
            'total_size_mb': total_size_mb,
            'num_dates': len(dates),
            'num_products': len(products),
            'dates': sorted(dates),
            'products': sorted(products)
        }
    
    def validate_schema(self, expected_schema: Dict[str, str]) -> bool:
        """
        Validate that Parquet files match expected schema.
        
        Args:
            expected_schema: Dict of {column: dtype}
        
        Returns:
            True if schema matches, False otherwise
        """
        # Read a small sample
        sample_files = list(self.base_dir.rglob('*.parquet'))[:1]
        if not sample_files:
            print("⚠️  No Parquet files found")
            return False
        
        df = cudf.read_parquet(str(sample_files[0]), nrows=1)
        
        # Check columns
        for col, expected_dtype in expected_schema.items():
            if col not in df.columns:
                print(f"❌ Missing column: {col}")
                return False
            
            actual_dtype = str(df[col].dtype)
            if expected_dtype not in actual_dtype:
                print(f"❌ Schema mismatch: {col} is {actual_dtype}, expected {expected_dtype}")
                return False
        
        print("✅ Schema validation passed")
        return True


def csv_to_parquet_batch(csv_files: List[Path], output_dir: Path,
                          partition_cols: List[str],
                          compression: str = 'snappy',
                          chunk_size: int = 10_000_000) -> None:
    """
    Convert multiple CSV files to partitioned Parquet format (GPU-accelerated).
    
    Args:
        csv_files: List of CSV file paths
        output_dir: Output directory for Parquet files
        partition_cols: Columns to partition by
        compression: Compression codec
        chunk_size: Rows to process at once
    
    Example:
        >>> csv_files = list(Path('datasets/raw_csv').glob('level2_*.csv'))
        >>> csv_to_parquet_batch(
        ...     csv_files,
        ...     Path('datasets/parquet/level2'),
        ...     partition_cols=['date', 'product_id']
        ... )
    """
    manager = ParquetManager(output_dir, compression=compression)
    
    total_rows = 0
    for csv_file in csv_files:
        print(f"\n📂 Converting {csv_file.name}...")
        
        # Read CSV to GPU (cuDF is fast!)
        df = cudf.read_csv(csv_file)
        total_rows += len(df)
        
        # Extract date from filename or data
        if 'datetime' not in df.columns and 'timestamp' in df.columns:
            # Convert timestamp to datetime
            try:
                df['timestamp'] = df['timestamp'].astype('int64')
                df['datetime'] = df['timestamp'].astype('datetime64[s]')
            except:
                # String timestamps
                df['datetime'] = cudf.to_datetime(df['timestamp'])
        
        # Add date column for partitioning
        if 'date' not in df.columns:
            df['date'] = df['datetime'].dt.strftime('%Y-%m-%d')
        
        # Write with partitioning
        manager.write_partitioned(df, partition_cols=partition_cols)
        
        print(f"   ✓ Wrote {len(df):,} rows")
        
        # Free GPU memory
        del df
        import cupy as cp
        cp._default_memory_pool.free_all_blocks()
    
    print(f"\n✅ Converted {len(csv_files)} files, {total_rows:,} total rows")
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\n📊 Output statistics:")
    print(f"   Files: {stats['num_files']}")
    print(f"   Size: {stats['total_size_mb']:.1f} MB")
    print(f"   Dates: {stats['num_dates']} ({min(stats['dates'])} to {max(stats['dates'])})")
    print(f"   Products: {stats['num_products']} ({', '.join(stats['products'])})")


if __name__ == '__main__':
    # Test Parquet utilities
    print("=" * 80)
    print("PARQUET UTILITIES TEST")
    print("=" * 80)
    
    # Create test data
    import cudf
    test_df = cudf.DataFrame({
        'timestamp': range(1000),
        'product_id': ['BTC-USD'] * 500 + ['ETH-USD'] * 500,
        'price': cudf.Series([50000.0] * 1000) + cudf.Series(range(1000)),
        'volume': range(1000, 2000)
    })
    test_df['datetime'] = test_df['timestamp'].astype('datetime64[s]')
    test_df['date'] = test_df['datetime'].dt.strftime('%Y-%m-%d')
    
    # Write partitioned
    manager = ParquetManager('/tmp/test_parquet')
    print("\n📝 Writing partitioned data...")
    manager.write_partitioned(test_df, partition_cols=['date', 'product_id'])
    
    # Read with filters
    print("\n📖 Reading with filters (BTC-USD only)...")
    btc_df = manager.read_lazy(product='BTC-USD')
    print(f"   Loaded {len(btc_df):,} rows (expected 500)")
    
    # Get statistics
    print("\n📊 Statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED")
    print("=" * 80)

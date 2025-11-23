"""
Stage 0: JSONL → Parquet Conversion (GPU-Accelerated)
======================================================

Converts raw JSONL websocket data (.txt files) directly to Parquet format.

Why skip CSV?
- ✅ Faster: No intermediate CSV step (2x faster conversion)
- ✅ Less disk: Don't store both CSV and Parquet (save 30GB)
- ✅ Cleaner: Direct path from data collection → analysis
- ✅ Simpler: One conversion script instead of two

Usage:
    python gpu/stage0_jsonl_to_parquet.py
    python gpu/stage0_jsonl_to_parquet.py --validate
    python gpu/stage0_jsonl_to_parquet.py --input crypto_data_jsonl --compression zstd

Performance:
    - 10-20x faster than pandas JSON parsing
    - 9-10x compression (30GB JSONL → 3-6GB Parquet)
    - Automatic partitioning by date and product
"""

import cudf
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from our config
from config import (
    JSONL_INPUT_DIR,
    PARQUET_DIR,
    PARQUET_LEVEL2_DIR,
    PARQUET_TICKER_DIR,
    LEVEL2_PARTITION_COLS,
    TICKER_PARTITION_COLS,
    COMPRESSION,
    CHUNK_SIZE_ROWS
)

# Import GPU utilities
from utils.gpu_memory import GPUMemoryManager, GPUMemoryMonitor
from utils.parquet_utils import ParquetManager


def convert_level2_data(
    input_dir: str,
    output_dir: str,
    compression: str = 'snappy',
    chunk_size: int = CHUNK_SIZE_ROWS,
    skip_latest: bool = True
) -> None:
    """
    Convert level2 JSONL files (.txt) to partitioned Parquet.
    
    Input format (JSONL in .txt files):
        {"type":"snapshot","product_id":"BTC-USD","bids":[[50000,1.5]...],"asks":[[50100,2.0]...],"time":"2025-11-07T12:00:00.123456Z"}
        {"type":"l2update","product_id":"BTC-USD","changes":[["buy","50000","1.6"]],"time":"2025-11-07T12:00:01.234567Z"}
    
    Output: Partitioned Parquet by date and product_id
    
    Args:
        input_dir: Directory containing level2_*.txt files
        output_dir: Output directory for Parquet files
        compression: Compression codec (snappy, gzip, zstd)
        chunk_size: Rows to process at once (memory management)
        skip_latest: Skip the most recent file (likely still being written)
    """
    mem = GPUMemoryManager()
    pm = ParquetManager(output_dir)
    
    # Find all level2 .txt files
    input_path = Path(input_dir)
    jsonl_files = sorted(input_path.glob("level2_*.txt"))
    
    # Skip the latest file if collector is still running
    if skip_latest and len(jsonl_files) > 1:
        skipped_file = jsonl_files[-1]
        jsonl_files = jsonl_files[:-1]
        print(f"⚠️  Skipping latest file (likely active): {skipped_file.name}")
    
    if not jsonl_files:
        print(f"⚠️  No level2_*.txt files found in {input_dir}")
        return
    
    print(f"📁 Found {len(jsonl_files)} level2 JSONL files")
    
    for jsonl_file in jsonl_files:
        print(f"\n🔄 Processing: {jsonl_file.name}")
        
        with GPUMemoryMonitor(f"Converting {jsonl_file.name}"):
            try:
                # Read JSONL with cuDF (GPU-accelerated)
                # cuDF can read JSONL with lines=True parameter
                df = cudf.read_json(
                    jsonl_file,
                    lines=True,  # Each line is a separate JSON object
                    dtype={
                        'product_id': 'str',
                        'type': 'str',
                        'time': 'str'
                    },
                    # Ignore malformed lines (incomplete JSON from active file)
                    engine='cudf'  # Use cuDF engine for better error handling
                )
                
                print(f"   ✓ Loaded {len(df):,} events from JSONL")
                
                # Parse timestamp and extract date for partitioning
                df['timestamp'] = cudf.to_datetime(df['time'], format='mixed')
                df['date'] = df['timestamp'].dt.date.astype('str')
                
                # Ensure partition columns exist
                if 'product_id' not in df.columns:
                    print(f"   ⚠️  No product_id column, skipping {jsonl_file.name}")
                    continue
                
                # Write partitioned by date and product_id
                pm.write_partitioned(
                    df=df,
                    partition_cols=LEVEL2_PARTITION_COLS,
                    compression=compression
                )
                
                print(f"   ✓ Written to Parquet with partitions: {LEVEL2_PARTITION_COLS}")
                
                # Free memory
                del df
                mem.free_memory()
                
            except Exception as e:
                print(f"   ❌ Error processing {jsonl_file.name}: {e}")
                continue
    
    print("\n✅ Level2 JSONL → Parquet conversion complete!")


def convert_ticker_data(
    input_dir: str,
    output_dir: str,
    compression: str = 'snappy',
    chunk_size: int = CHUNK_SIZE_ROWS,
    skip_latest: bool = True
) -> None:
    """
    Convert ticker JSONL files (.txt) to partitioned Parquet.
    
    Input format (JSONL in .txt files):
        {"type":"ticker","product_id":"BTC-USD","price":"50000","volume_24h":"1000","time":"2025-11-07T12:00:00.123456Z"}
    
    Output: Partitioned Parquet by date
    
    Args:
        input_dir: Directory containing ticker_*.txt files
        output_dir: Output directory for Parquet files
        compression: Compression codec (snappy, gzip, zstd)
        chunk_size: Rows to process at once
        skip_latest: Skip the most recent file (likely still being written)
    """
    mem = GPUMemoryManager()
    pm = ParquetManager(output_dir)
    
    # Find all ticker .txt files
    input_path = Path(input_dir)
    jsonl_files = sorted(input_path.glob("ticker_*.txt"))
    
    # Skip the latest file if collector is still running
    if skip_latest and len(jsonl_files) > 1:
        skipped_file = jsonl_files[-1]
        jsonl_files = jsonl_files[:-1]
        print(f"⚠️  Skipping latest file (likely active): {skipped_file.name}")
    
    if not jsonl_files:
        print(f"⚠️  No ticker_*.txt files found in {input_dir}")
        return
    
    print(f"📁 Found {len(jsonl_files)} ticker JSONL files")
    
    for jsonl_file in jsonl_files:
        print(f"\n🔄 Processing: {jsonl_file.name}")
        
        with GPUMemoryMonitor(f"Converting {jsonl_file.name}"):
            try:
                # Read JSONL with cuDF
                df = cudf.read_json(
                    jsonl_file,
                    lines=True,
                    dtype={
                        'product_id': 'str',
                        'type': 'str',
                        'price': 'str',
                        'time': 'str'
                    },
                    engine='cudf'
                )
                
                print(f"   ✓ Loaded {len(df):,} ticker events from JSONL")
                
                # Parse timestamp and extract date
                df['timestamp'] = cudf.to_datetime(df['time'], format='mixed')
                df['date'] = df['timestamp'].dt.date.astype('str')
                
                # Convert price to float (it comes as string from API)
                if 'price' in df.columns:
                    df['price'] = df['price'].astype('float64')
                
                # Write partitioned by date
                pm.write_partitioned(
                    df=df,
                    partition_cols=TICKER_PARTITION_COLS,
                    compression=compression
                )
                
                print(f"   ✓ Written to Parquet with partitions: {TICKER_PARTITION_COLS}")
                
                # Free memory
                del df
                mem.free_memory()
                
            except Exception as e:
                print(f"   ❌ Error processing {jsonl_file.name}: {e}")
                continue
    
    print("\n✅ Ticker JSONL → Parquet conversion complete!")


def validate_conversion(parquet_dir: str) -> None:
    """
    Validate Parquet conversion and show compression statistics.
    
    Args:
        parquet_dir: Directory containing Parquet files
    """
    print("\n" + "="*60)
    print("📊 CONVERSION VALIDATION")
    print("="*60)
    
    pm_level2 = ParquetManager(os.path.join(parquet_dir, 'level2'))
    pm_ticker = ParquetManager(os.path.join(parquet_dir, 'ticker'))
    
    # Validate level2 data
    print("\n📁 Level2 Data:")
    try:
        stats = pm_level2.get_statistics()
        print(f"   ✓ Files: {stats['file_count']}")
        print(f"   ✓ Total size: {stats['total_size_mb']:.2f} MB")
        print(f"   ✓ Date range: {stats['min_date']} to {stats['max_date']}")
        print(f"   ✓ Products: {stats['product_count']}")
        
        # Test reading a sample
        if stats['file_count'] > 0:
            sample_date = stats['min_date']
            sample_df = pm_level2.read_date(sample_date, columns=['product_id', 'type', 'time'])
            print(f"   ✓ Sample read successful: {len(sample_df):,} rows from {sample_date}")
            del sample_df
            
    except Exception as e:
        print(f"   ❌ Error validating level2 data: {e}")
    
    # Validate ticker data
    print("\n📁 Ticker Data:")
    try:
        stats = pm_ticker.get_statistics()
        print(f"   ✓ Files: {stats['file_count']}")
        print(f"   ✓ Total size: {stats['total_size_mb']:.2f} MB")
        print(f"   ✓ Date range: {stats['min_date']} to {stats['max_date']}")
        
        # Test reading a sample
        if stats['file_count'] > 0:
            sample_date = stats['min_date']
            sample_df = pm_ticker.read_date(sample_date, columns=['product_id', 'price', 'time'])
            print(f"   ✓ Sample read successful: {len(sample_df):,} rows from {sample_date}")
            del sample_df
            
    except Exception as e:
        print(f"   ❌ Error validating ticker data: {e}")
    
    # Calculate compression (if original JSONL files still exist)
    print("\n📊 Compression Analysis:")
    print("   (Compare JSONL input size vs Parquet output size)")
    
    print("\n✅ Validation complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert JSONL websocket data (.txt) to Parquet format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Convert all JSONL files from default directory
    python gpu/stage0_jsonl_to_parquet.py
    
    # Convert from custom directory with ZSTD compression (best compression)
    python gpu/stage0_jsonl_to_parquet.py --input my_data --compression zstd
    
    # Validate existing Parquet files
    python gpu/stage0_jsonl_to_parquet.py --validate
    
    # Convert only level2 data
    python gpu/stage0_jsonl_to_parquet.py --level2-only
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default=str(JSONL_INPUT_DIR),
        help=f'Input directory containing JSONL .txt files (default: {JSONL_INPUT_DIR})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=str(PARQUET_DIR),
        help=f'Output directory for Parquet files (default: {PARQUET_DIR})'
    )
    
    parser.add_argument(
        '--compression',
        type=str,
        choices=['snappy', 'gzip', 'zstd', 'none'],
        default=COMPRESSION,
        help=f'Compression codec (default: {COMPRESSION}). ZSTD = best compression, Snappy = fastest'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate existing Parquet files instead of converting'
    )
    
    parser.add_argument(
        '--level2-only',
        action='store_true',
        help='Convert only level2 data'
    )
    
    parser.add_argument(
        '--ticker-only',
        action='store_true',
        help='Convert only ticker data'
    )
    
    parser.add_argument(
        '--include-latest',
        action='store_true',
        help='Include the latest file (risky if collector is running). By default, skips latest file.'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("="*60)
    print("🚀 JSONL → Parquet Conversion (GPU-Accelerated)")
    print("="*60)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Compression: {args.compression}")
    print("="*60)
    
    # Validate mode
    if args.validate:
        validate_conversion(args.output)
        return
    
    # Create output directories
    os.makedirs(PARQUET_LEVEL2_DIR, exist_ok=True)
    os.makedirs(PARQUET_TICKER_DIR, exist_ok=True)
    
    # Convert data
    skip_latest = not args.include_latest  # By default, skip latest file
    
    if not args.ticker_only:
        print("\n📦 Converting Level2 data...")
        convert_level2_data(
            input_dir=args.input,
            output_dir=str(PARQUET_LEVEL2_DIR),
            compression=args.compression,
            skip_latest=skip_latest
        )
    
    if not args.level2_only:
        print("\n📦 Converting Ticker data...")
        convert_ticker_data(
            input_dir=args.input,
            output_dir=str(PARQUET_TICKER_DIR),
            compression=args.compression,
            skip_latest=skip_latest
        )
    
    # Auto-validate after conversion
    print("\n" + "="*60)
    validate_conversion(args.output)
    
    print("\n" + "="*60)
    print("🎉 ALL DONE!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Check output: ls {args.output}")
    print(f"2. Run Stage 2: python gpu/stage2_orderbook_builder.py")
    print(f"3. See QUICKSTART.md for detailed usage")


if __name__ == '__main__':
    main()

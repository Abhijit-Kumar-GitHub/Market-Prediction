#!/usr/bin/env python3
"""
JSONL to Parquet Converter - CPU ONLY Version
For running on local machines without GPU

Converts raw JSONL websocket data (.txt files) directly to Parquet format.
Uses pandas (CPU) instead of cuDF (GPU).

Expected Performance:
- CPU (pandas): ~5-10 min per file (vs ~30 seconds with GPU)
- Memory: ~4-8GB RAM recommended
- Works on any machine (no GPU required)

Usage:
    python scripts/jsonl_to_parquet_CPU.py
    python scripts/jsonl_to_parquet_CPU.py --skip-latest  # Skip most recent file
    python scripts/jsonl_to_parquet_CPU.py --validate     # Validate existing files
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse
import time

# CPU libraries (no GPU required!)
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import configuration
try:
    from config.gpu_config import (
        JSONL_INPUT_DIR,
        PARQUET_LEVEL2_DIR,
        PARQUET_TICKER_DIR,
        COMPRESSION
    )
except ImportError as e:
    # Fallback to default paths
    print(f"Warning: Could not import config, using defaults")
    JSONL_INPUT_DIR = Path('crypto_data_jsonl')
    PARQUET_LEVEL2_DIR = Path('datasets/parquet/level2')
    PARQUET_TICKER_DIR = Path('datasets/parquet/ticker')
    COMPRESSION = 'snappy'


def flatten_level2_line(line: str) -> List[Dict[str, Any]]:
    """
    Flatten a single level2 JSONL line into multiple rows.
    Same logic as GPU version, just uses standard Python.
    """
    try:
        data = json.loads(line)
        
        timestamp = data.get('timestamp', '')
        channel = data.get('channel', '')
        sequence_num = data.get('sequence_num', 0)
        
        rows = []
        for event in data.get('events', []):
            event_type = event.get('type', '')
            product_id = event.get('product_id', '')
            
            for update in event.get('updates', []):
                row = {
                    'timestamp': timestamp,
                    'channel': channel,
                    'sequence_num': sequence_num,
                    'event_type': event_type,
                    'product_id': product_id,
                    'side': update.get('side', ''),
                    'event_time': update.get('event_time', ''),
                    'price_level': update.get('price_level', ''),
                    'new_quantity': update.get('new_quantity', '')
                }
                rows.append(row)
        
        return rows
    
    except (json.JSONDecodeError, KeyError, Exception):
        return []


def flatten_ticker_line(line: str) -> List[Dict[str, Any]]:
    """
    Flatten a single ticker JSONL line into multiple rows.
    """
    try:
        data = json.loads(line)
        
        timestamp = data.get('timestamp', '')
        channel = data.get('channel', '')
        sequence_num = data.get('sequence_num', 0)
        
        rows = []
        for event in data.get('events', []):
            event_type = event.get('type', '')
            
            for ticker in event.get('tickers', []):
                row = {
                    'timestamp': timestamp,
                    'channel': channel,
                    'sequence_num': sequence_num,
                    'event_type': event_type,
                    'product_id': ticker.get('product_id', ''),
                    'price': ticker.get('price', ''),
                    'volume_24_h': ticker.get('volume_24_h', ''),
                    'low_24_h': ticker.get('low_24_h', ''),
                    'high_24_h': ticker.get('high_24_h', ''),
                    'low_52_w': ticker.get('low_52_w', ''),
                    'high_52_w': ticker.get('high_52_w', ''),
                    'price_percent_chg_24_h': ticker.get('price_percent_chg_24_h', ''),
                    'best_bid': ticker.get('best_bid', ''),
                    'best_ask': ticker.get('best_ask', ''),
                    'best_bid_quantity': ticker.get('best_bid_quantity', ''),
                    'best_ask_quantity': ticker.get('best_ask_quantity', '')
                }
                rows.append(row)
        
        return rows
    
    except (json.JSONDecodeError, KeyError, Exception):
        return []


def convert_level2_data_cpu(
        input_dir: str,
        output_dir: str,
        compression: str = "snappy",
        skip_latest: bool = True,
        write_csv: bool = False
):
    """
    Convert Level2 JSONL files to Parquet format using pandas (CPU).
    Uses streaming write approach to minimize RAM usage.
    
    Args:
        input_dir: Directory containing JSONL files
        output_dir: Directory to write Parquet files
        compression: Compression codec (snappy, gzip, zstd)
        skip_latest: If True, skip the most recent file
        write_csv: If True, also write CSV files alongside Parquet
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all level2 JSONL files
    jsonl_files = sorted(input_path.glob("level2_*.txt"))
    
    if not jsonl_files:
        print(f"No level2 JSONL files found in {input_dir}")
        return
    
    # Skip the latest file if requested
    if skip_latest and len(jsonl_files) > 1:
        skipped_file = jsonl_files[-1]
        jsonl_files = jsonl_files[:-1]
        print(f"Skipping latest file (likely active): {skipped_file.name}")
    
    print(f"Found {len(jsonl_files)} level2 JSONL files\n")
    
    # Schema definition - enforced for all chunks
    TARGET_DTYPES = {
        'price_level': 'float64',
        'new_quantity': 'float64',
        'sequence_num': 'int64',
        'channel': 'object',
        'event_type': 'object',
        'product_id': 'object',
        'side': 'object'
    }
    
    # Define PyArrow schema once (reused for all chunks)
    # CRITICAL: Use string() NOT dictionary to ensure schema compatibility across files
    def get_parquet_schema():
        return pa.schema([
            pa.field('timestamp', pa.timestamp('ns', tz='UTC')),
            pa.field('channel', pa.string()),
            pa.field('sequence_num', pa.int64()),
            pa.field('event_type', pa.string()),
            pa.field('product_id', pa.string()),
            pa.field('side', pa.string()),
            pa.field('event_time', pa.timestamp('ns', tz='UTC')),
            pa.field('price_level', pa.float64()),
            pa.field('new_quantity', pa.float64()),
            pa.field('date', pa.string())
        ])
    
    for jsonl_file in jsonl_files:
        print(f"Processing: {jsonl_file.name}")
        file_start = time.perf_counter()
        
        try:
            # Extract date from filename
            date_str = jsonl_file.stem.split('_')[1]
            date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            
            # Streaming approach: Process in small chunks and write immediately
            # This prevents loading all 48M rows into RAM at once
            CHUNK_LINES = 50_000  # Reduced from 200K for safer memory usage
            
            line_count = 0
            error_count = 0
            chunk_rows = []
            total_rows_written = 0
            chunk_num = 0
            
            # Track Parquet writers per product (for appending)
            parquet_writers = {}  # {product_id: ParquetWriter}
            product_schemas = {}  # {product_id: schema}
            product_row_counts = {}  # {product_id: count}
            
            schema = get_parquet_schema()
            
            print(f"  Processing & writing in chunks of {CHUNK_LINES:,} lines...")
            print(f"  (Streaming mode: no large DataFrame concatenation)")
            
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line_count += 1
                    if not line.strip():
                        continue
                    
                    rows = flatten_level2_line(line)
                    if not rows and line.strip():
                        error_count += 1
                    chunk_rows.extend(rows)
                    
                    # Process and write chunk every CHUNK_LINES
                    if line_count % CHUNK_LINES == 0 and chunk_rows:
                        chunk_num += 1
                        chunk_df = pd.DataFrame(chunk_rows)
                        chunk_df = chunk_df.astype(TARGET_DTYPES)
                        chunk_df['date'] = date
                        
                        # Convert timestamps
                        chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed', utc=True, errors='coerce')
                        chunk_df['event_time'] = pd.to_datetime(chunk_df['event_time'], format='mixed', utc=True, errors='coerce')
                        
                        # Write each product's data immediately (streaming write)
                        for product_id in chunk_df['product_id'].unique():
                            product_data = chunk_df[chunk_df['product_id'] == product_id].copy()
                            
                            # Create partition directory
                            partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                            partition_dir.mkdir(parents=True, exist_ok=True)
                            output_file = partition_dir / "data.parquet"
                            
                            # Convert to PyArrow table
                            table = pa.Table.from_pandas(product_data, schema=schema, preserve_index=False)
                            
                            # Append to existing file or create new
                            if product_id not in parquet_writers:
                                # First write for this product - create new file
                                # use_dictionary=False prevents inconsistent dictionary encoding
                                parquet_writers[product_id] = pq.ParquetWriter(
                                    output_file, 
                                    schema, 
                                    compression=compression,
                                    use_dictionary=False  # CRITICAL: Prevent dictionary encoding issues
                                )
                                product_row_counts[product_id] = 0
                            
                            # Write chunk to file
                            parquet_writers[product_id].write_table(table)
                            product_row_counts[product_id] += len(product_data)
                        
                        total_rows_written += len(chunk_rows)
                        print(f"    Chunk {chunk_num}: Processed {line_count:,} lines, wrote {total_rows_written:,} rows")
                        chunk_rows = []  # Clear for next chunk
            
            # Process remaining rows
            if chunk_rows:
                chunk_num += 1
                chunk_df = pd.DataFrame(chunk_rows)
                chunk_df = chunk_df.astype(TARGET_DTYPES)
                chunk_df['date'] = date
                
                chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed', utc=True, errors='coerce')
                chunk_df['event_time'] = pd.to_datetime(chunk_df['event_time'], format='mixed', utc=True, errors='coerce')
                
                for product_id in chunk_df['product_id'].unique():
                    product_data = chunk_df[chunk_df['product_id'] == product_id].copy()
                    
                    partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                    partition_dir.mkdir(parents=True, exist_ok=True)
                    output_file = partition_dir / "data.parquet"
                    
                    table = pa.Table.from_pandas(product_data, schema=schema, preserve_index=False)
                    
                    if product_id not in parquet_writers:
                        parquet_writers[product_id] = pq.ParquetWriter(
                            output_file, 
                            schema, 
                            compression=compression
                        )
                        product_row_counts[product_id] = 0
                    
                    parquet_writers[product_id].write_table(table)
                    product_row_counts[product_id] += len(product_data)
                
                total_rows_written += len(chunk_rows)
                print(f"    Final chunk {chunk_num}: Processed {line_count:,} lines, wrote {total_rows_written:,} rows")
            
            # Close all writers
            print(f"  Finalizing {len(parquet_writers)} product files...")
            for product_id, writer in parquet_writers.items():
                writer.close()
                
                # Get file size
                partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                output_file = partition_dir / "data.parquet"
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                row_count = product_row_counts[product_id]
                print(f"    ✓ {product_id}: {row_count:,} rows ({file_size_mb:.2f} MB)")
            
            if error_count > 0:
                print(f"  Skipped {error_count} malformed lines out of {line_count}")
            
            print(f"  ✓ Total rows written: {total_rows_written:,}")
            
            file_elapsed = time.perf_counter() - file_start
            print(f"  File time: {file_elapsed:.2f}s\n")
            
        except Exception as e:
            print(f"Error processing {jsonl_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue


def convert_ticker_data_cpu(
        input_dir: str,
        output_dir: str,
        compression: str = "snappy",
        skip_latest: bool = True,
        write_csv: bool = False
):
    """
    Convert Ticker JSONL files to Parquet format using pandas (CPU).
    Uses streaming write approach to minimize RAM usage.
    
    Args:
        input_dir: Directory containing JSONL files
        output_dir: Directory to write Parquet files
        compression: Compression codec (snappy, gzip, zstd)
        skip_latest: If True, skip the most recent file
        write_csv: If True, also write CSV files alongside Parquet
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all ticker JSONL files
    jsonl_files = sorted(input_path.glob("ticker_*.txt"))
    
    if not jsonl_files:
        print(f"No ticker JSONL files found in {input_dir}")
        return
    
    # Skip the latest file if requested
    if skip_latest and len(jsonl_files) > 1:
        skipped_file = jsonl_files[-1]
        jsonl_files = jsonl_files[:-1]
        print(f"Skipping latest file (likely active): {skipped_file.name}")
    
    print(f"Found {len(jsonl_files)} ticker JSONL files\n")
    
    TARGET_DTYPES_TICKER = {
        'price': 'float64',
        'volume_24_h': 'float64',
        'low_24_h': 'float64',
        'high_24_h': 'float64',
        'low_52_w': 'float64',
        'high_52_w': 'float64',
        'price_percent_chg_24_h': 'float64',
        'best_bid': 'float64',
        'best_ask': 'float64',
        'best_bid_quantity': 'float64',
        'best_ask_quantity': 'float64',
        'sequence_num': 'int64',
        'channel': 'object',
        'event_type': 'object',
        'product_id': 'object',
        'date': 'object'
    }
    
    # Define PyArrow schema for ticker data
    # CRITICAL: Use string() NOT dictionary to ensure schema compatibility
    def get_ticker_parquet_schema():
        return pa.schema([
            pa.field('timestamp', pa.timestamp('ns', tz='UTC')),
            pa.field('channel', pa.string()),
            pa.field('sequence_num', pa.int64()),
            pa.field('event_type', pa.string()),
            pa.field('product_id', pa.string()),
            pa.field('price', pa.float64()),
            pa.field('volume_24_h', pa.float64()),
            pa.field('low_24_h', pa.float64()),
            pa.field('high_24_h', pa.float64()),
            pa.field('low_52_w', pa.float64()),
            pa.field('high_52_w', pa.float64()),
            pa.field('price_percent_chg_24_h', pa.float64()),
            pa.field('best_bid', pa.float64()),
            pa.field('best_ask', pa.float64()),
            pa.field('best_bid_quantity', pa.float64()),
            pa.field('best_ask_quantity', pa.float64()),
            pa.field('date', pa.string())
        ])
    
    for jsonl_file in jsonl_files:
        print(f"Processing: {jsonl_file.name}")
        file_start = time.perf_counter()
        
        try:
            # Extract date from filename
            date_str = jsonl_file.stem.split('_')[1]
            date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            
            # Streaming approach: Process in small chunks and write immediately
            CHUNK_LINES = 50_000
            
            line_count = 0
            error_count = 0
            chunk_rows = []
            total_rows_written = 0
            chunk_num = 0
            
            # Track Parquet writers per product
            parquet_writers = {}
            product_row_counts = {}
            
            schema = get_ticker_parquet_schema()
            
            print(f"  Processing & writing in chunks of {CHUNK_LINES:,} lines...")
            print(f"  (Streaming mode: no large DataFrame concatenation)")
            
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line_count += 1
                    if not line.strip():
                        continue
                    
                    rows = flatten_ticker_line(line)
                    if not rows and line.strip():
                        error_count += 1
                    chunk_rows.extend(rows)
                    
                    # Process and write chunk every CHUNK_LINES
                    if line_count % CHUNK_LINES == 0 and chunk_rows:
                        chunk_num += 1
                        chunk_df = pd.DataFrame(chunk_rows)
                        
                        # Apply type conversions
                        for col, dtype in TARGET_DTYPES_TICKER.items():
                            if col in chunk_df.columns and col != 'date':
                                try:
                                    if chunk_df[col].dtype != dtype:
                                        chunk_df[col] = chunk_df[col].astype(dtype)
                                except (ValueError, TypeError):
                                    pass
                        
                        chunk_df['date'] = date
                        chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed', utc=True, errors='coerce')
                        
                        # Write each product's data immediately
                        for product_id in chunk_df['product_id'].unique():
                            product_data = chunk_df[chunk_df['product_id'] == product_id].copy()
                            
                            partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                            partition_dir.mkdir(parents=True, exist_ok=True)
                            output_file = partition_dir / "data.parquet"
                            
                            table = pa.Table.from_pandas(product_data, schema=schema, preserve_index=False)
                            
                            if product_id not in parquet_writers:
                                # use_dictionary=False prevents inconsistent dictionary encoding
                                parquet_writers[product_id] = pq.ParquetWriter(
                                    output_file, 
                                    schema, 
                                    compression=compression,
                                    use_dictionary=False  # CRITICAL: Prevent dictionary encoding issues
                                )
                                product_row_counts[product_id] = 0
                            
                            parquet_writers[product_id].write_table(table)
                            product_row_counts[product_id] += len(product_data)
                        
                        total_rows_written += len(chunk_rows)
                        print(f"    Chunk {chunk_num}: Processed {line_count:,} lines, wrote {total_rows_written:,} rows")
                        chunk_rows = []
            
            # Process remaining rows
            if chunk_rows:
                chunk_num += 1
                chunk_df = pd.DataFrame(chunk_rows)
                
                for col, dtype in TARGET_DTYPES_TICKER.items():
                    if col in chunk_df.columns and col != 'date':
                        try:
                            if chunk_df[col].dtype != dtype:
                                chunk_df[col] = chunk_df[col].astype(dtype)
                        except (ValueError, TypeError):
                            pass
                
                chunk_df['date'] = date
                chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed', utc=True, errors='coerce')
                
                for product_id in chunk_df['product_id'].unique():
                    product_data = chunk_df[chunk_df['product_id'] == product_id].copy()
                    
                    partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                    partition_dir.mkdir(parents=True, exist_ok=True)
                    output_file = partition_dir / "data.parquet"
                    
                    table = pa.Table.from_pandas(product_data, schema=schema, preserve_index=False)
                    
                    if product_id not in parquet_writers:
                        # use_dictionary=False prevents inconsistent dictionary encoding
                        parquet_writers[product_id] = pq.ParquetWriter(
                            output_file, 
                            schema, 
                            compression=compression,
                            use_dictionary=False  # CRITICAL: Prevent dictionary encoding issues
                        )
                        product_row_counts[product_id] = 0
                    
                    parquet_writers[product_id].write_table(table)
                    product_row_counts[product_id] += len(product_data)
                
                total_rows_written += len(chunk_rows)
                print(f"    Final chunk {chunk_num}: Processed {line_count:,} lines, wrote {total_rows_written:,} rows")
            
            # Close all writers
            print(f"  Finalizing {len(parquet_writers)} product files...")
            for product_id, writer in parquet_writers.items():
                writer.close()
                
                partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                output_file = partition_dir / "data.parquet"
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                row_count = product_row_counts[product_id]
                print(f"    ✓ {product_id}: {row_count:,} rows ({file_size_mb:.2f} MB)")
            
            if error_count > 0:
                print(f"  Skipped {error_count} malformed lines out of {line_count}")
            
            print(f"  ✓ Total rows written: {total_rows_written:,}")
            
            file_elapsed = time.perf_counter() - file_start
            print(f"  File time: {file_elapsed:.2f}s\n")
            
        except Exception as e:
            print(f"Error processing {jsonl_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue


def validate_conversion(parquet_dir: str):
    """
    Validate converted Parquet files.
    """
    print("=" * 60)
    print("CONVERSION VALIDATION")
    print("=" * 60)
    print()
    
    parquet_path = Path(parquet_dir)
    
    # Check Level2 data
    level2_dir = parquet_path / "level2"
    if level2_dir.exists():
        level2_files = list(level2_dir.rglob("*.parquet"))
        print(f"Level2 Data:")
        print(f"  Files: {len(level2_files)}")
        
        if level2_files:
            total_rows = 0
            total_size = 0
            # Read files individually to avoid schema merge issues
            for file in level2_files:
                try:
                    # Read metadata only for speed
                    parquet_file = pq.ParquetFile(file)
                    total_rows += parquet_file.metadata.num_rows
                    total_size += file.stat().st_size
                except Exception as e:
                    print(f"  Warning: Could not read {file.name}: {e}")
            
            print(f"  Total Rows: {total_rows:,}")
            print(f"  Total Size: {total_size / (1024 ** 2):.2f} MB")
            print(f"  Avg File Size: {total_size / len(level2_files) / (1024 ** 2):.2f} MB")
    else:
        print("Level2 Data: Not found")
    
    print()
    
    # Check Ticker data
    ticker_dir = parquet_path / "ticker"
    if ticker_dir.exists():
        ticker_files = list(ticker_dir.rglob("*.parquet"))
        print(f"Ticker Data:")
        print(f"  Files: {len(ticker_files)}")
        
        if ticker_files:
            total_rows = 0
            total_size = 0
            # Read files individually to avoid schema merge issues
            for file in ticker_files:
                try:
                    # Read metadata only for speed
                    parquet_file = pq.ParquetFile(file)
                    total_rows += parquet_file.metadata.num_rows
                    total_size += file.stat().st_size
                except Exception as e:
                    print(f"  Warning: Could not read {file.name}: {e}")
            
            print(f"  Total Rows: {total_rows:,}")
            print(f"  Total Size: {total_size / (1024 ** 2):.2f} MB")
            print(f"  Avg File Size: {total_size / len(ticker_files) / (1024 ** 2):.2f} MB")
    else:
        print("Ticker Data: Not found")
    
    print()
    print("Validation complete!")


def main():
    """Main entry point for CPU-based JSONL → Parquet conversion."""
    parser = argparse.ArgumentParser(
        description="Convert JSONL websocket data to Parquet format (CPU version)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(JSONL_INPUT_DIR),
        help="Input directory containing JSONL files"
    )
    parser.add_argument(
        "--compression",
        type=str,
        default=COMPRESSION,
        choices=["snappy", "gzip", "zstd"],
        help="Compression codec for Parquet files"
    )
    parser.add_argument(
        "--skip-latest",
        action="store_true",
        help="Skip the latest file (recommended if collector is running)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing Parquet files instead of converting"
    )
    parser.add_argument(
        "--write-csv",
        action="store_true",
        help="Also write CSV files alongside Parquet (for Power BI compatibility)"
    )
    
    args = parser.parse_args()
    
    # Validation mode
    if args.validate:
        validate_conversion(str(PARQUET_LEVEL2_DIR.parent))
        return
    
    # Print header
    print("=" * 60)
    print("JSONL → Parquet Conversion (CPU Version)")
    print("=" * 60)
    print(f"Input:  {args.input_dir}")
    print(f"Output: {PARQUET_LEVEL2_DIR.parent}")
    print(f"Compression: {args.compression}")
    print(f"Mode: CPU (pandas + PyArrow)")
    print("=" * 60)
    print()
    
    # Start overall timer
    total_start = time.perf_counter()
    
    # Convert Level2 data
    print("Converting Level2 data...")
    if args.write_csv:
        print("CSV export enabled")
    level_start = time.perf_counter()
    convert_level2_data_cpu(
        input_dir=args.input_dir,
        output_dir=str(PARQUET_LEVEL2_DIR),
        compression=args.compression,
        skip_latest=args.skip_latest,
        write_csv=args.write_csv
    )
    level_elapsed = time.perf_counter() - level_start
    print(f"Level2 conversion time: {level_elapsed:.2f}s")
    
    print("\n" + "=" * 60 + "\n")
    
    # Convert Ticker data
    print("Converting Ticker data...")
    ticker_start = time.perf_counter()
    convert_ticker_data_cpu(
        input_dir=args.input_dir,
        output_dir=str(PARQUET_TICKER_DIR),
        compression=args.compression,
        skip_latest=args.skip_latest,
        write_csv=args.write_csv
    )
    ticker_elapsed = time.perf_counter() - ticker_start
    print(f"Ticker conversion time: {ticker_elapsed:.2f}s")
    
    print("\n" + "=" * 60)
    print()
    
    # Validate conversion
    validate_conversion(str(PARQUET_LEVEL2_DIR.parent))
    
    total_elapsed = time.perf_counter() - total_start
    print(f"\nTotal conversion time: {total_elapsed:.2f}s ({total_elapsed/60:.1f} minutes)")
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("  1. Use the legacy CPU pipeline for further processing:")
    print("     - _archive_old_structure/legacy_data_pipeline/stage2_orderbook_builder.py")
    print("     - _archive_old_structure/legacy_data_pipeline/stage3_ml_features.py")
    print("  2. Or wait to run notebooks on Kaggle GPU")
    print("=" * 60)


if __name__ == "__main__":
    main()

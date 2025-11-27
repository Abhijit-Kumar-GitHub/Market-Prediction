#!/usr/bin/env python3
"""
Stage 0: JSONL → Parquet Conversion (GPU-Accelerated) - Fixed for Nested JSON

Converts raw JSONL websocket data (.txt files) directly to Parquet format.
Handles nested JSON structure from Coinbase WebSocket feed.

FIXED: Properly flattens nested JSON structure from Coinbase WebSocket API
- Level2: channel -> events -> updates (multiple rows per line)
- Ticker: channel -> events -> tickers (multiple rows per line)

Usage:
    python jsonl_to_parquet_v2.py                    # Skip latest file (safe)
    python jsonl_to_parquet_v2.py --include-latest   # Include all files (risky)
    python jsonl_to_parquet_v2.py --validate         # Validate existing Parquet
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# Add script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# GPU libraries
import cudf
import cupy as cp

# Import configuration
from config import (
    JSONL_INPUT_DIR,
    PARQUET_LEVEL2_DIR,
    PARQUET_TICKER_DIR,
    COMPRESSION
)

# Import GPU utilities
from utils.gpu_memory import GPUMemoryMonitor


def flatten_level2_line(line: str) -> List[Dict[str, Any]]:
    """
    Flatten a single level2 JSONL line into multiple rows.
    
    Input structure:
    {
        "channel": "l2_data",
        "timestamp": "2025-11-07T09:59:01.328203255Z",
        "sequence_num": 19,
        "events": [{
            "type": "update",
            "product_id": "BTC-USD",
            "updates": [
                {
                    "side": "bid",
                    "event_time": "2025-11-07T09:59:00.692602Z",
                    "price_level": "100877.72",
                    "new_quantity": "0.00198"
                }
            ]
        }]
    }
    
    Output: List of flat dictionaries, one per update
    """
    try:
        data = json.loads(line)
        
        # Extract top-level metadata
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
    
    except Exception:
        # Return empty list on error (skip malformed lines)
        return []


def flatten_ticker_line(line: str) -> List[Dict[str, Any]]:
    """
    Flatten a single ticker JSONL line into multiple rows.
    
    Input structure:
    {
        "channel": "ticker",
        "timestamp": "2025-11-07T09:58:59.715528253Z",
        "sequence_num": 0,
        "events": [{
            "type": "snapshot",
            "tickers": [{
                "type": "ticker",
                "product_id": "BTC-USD",
                "price": "100898",
                "volume_24_h": "9732.34623688",
                ...
            }]
        }]
    }
    
    Output: List of flat dictionaries, one per ticker
    """
    try:
        data = json.loads(line)
        
        # Extract top-level metadata
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
    
    except Exception:
        # Return empty list on error
        return []


def convert_level2_data(
    input_dir: str,
    output_dir: str,
    compression: str = "snappy",
    skip_latest: bool = True,
    write_csv: bool = False
):
    """
    Convert Level2 JSONL files to Parquet format.
    Handles nested JSON structure by flattening line-by-line.
    
    Args:
        input_dir: Directory containing JSONL files
        output_dir: Directory to write Parquet files
        compression: Compression codec (snappy, gzip, zstd)
        skip_latest: If True, skip the most recent file (likely being written)
        write_csv: If True, also write CSV files alongside Parquet
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all level2 JSONL files, sorted by name (which includes date)
    jsonl_files = sorted(input_path.glob("level2_*.txt"))
    
    if not jsonl_files:
        print(f"⚠️  No level2 JSONL files found in {input_dir}")
        return
    
    # Skip the latest file if requested (likely being actively written)
    if skip_latest and len(jsonl_files) > 1:
        skipped_file = jsonl_files[-1]
        jsonl_files = jsonl_files[:-1]
        print(f"⚠️  Skipping latest file (likely active): {skipped_file.name}")
    
    print(f"📁 Found {len(jsonl_files)} level2 JSONL files\n")
    
    for jsonl_file in jsonl_files:
        print(f"🔄 Processing: {jsonl_file.name}\n")
        
        # Extract date from filename (e.g., level2_20251107.txt -> 20251107)
        date_str = jsonl_file.stem.split('_')[1]
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        
        monitor = GPUMemoryMonitor(f"Converting {jsonl_file.name}")
        
        try:
            with monitor:
                # Flatten nested JSON structure line-by-line (memory-efficient)
                flattened_rows = []
                
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        rows = flatten_level2_line(line)
                        flattened_rows.extend(rows)
                
                if not flattened_rows:
                    print(f"   ⚠️  No valid data found in {jsonl_file.name}")
                    continue
                
                print(f"   ✓ Flattened {len(flattened_rows):,} orderbook updates from JSONL")
                
                # Use a dictionary to collect all chunks for a given product
                # This avoids repeated Parquet read/write/concat which causes schema conflicts
                from typing import Dict, List
                product_chunks: Dict[str, List] = {}
                
                # Process in chunks to avoid GPU OOM (10M rows at a time)
                chunk_size = 10_000_000
                
                for chunk_start in range(0, len(flattened_rows), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(flattened_rows))
                    chunk_rows = flattened_rows[chunk_start:chunk_end]
                    
                    # Convert chunk to cuDF DataFrame
                    df = cudf.DataFrame(chunk_rows)
                    
                    # Add date column for partitioning
                    df['date'] = date
                    
                    # Convert timestamps to datetime (handle mixed formats)
                    # Convert to pandas temporarily for robust datetime parsing, then back to cuDF
                    df_timestamp = df['timestamp'].to_pandas()
                    df_event_time = df['event_time'].to_pandas()
                    
                    import pandas as pd
                    df['timestamp'] = cudf.from_pandas(pd.to_datetime(df_timestamp, format='mixed', utc=True))
                    df['event_time'] = cudf.from_pandas(pd.to_datetime(df_event_time, format='mixed', utc=True))
                    
                    # Enforce strict schema on all columns to avoid concat issues
                    TARGET_DTYPES = {
                        'price_level': 'float64',
                        'new_quantity': 'float64',
                        'sequence_num': 'int64',
                        'channel': 'object',
                        'event_type': 'object',
                        'product_id': 'object',
                        'side': 'object',
                        'date': 'object'
                    }
                    
                    for col, dtype in TARGET_DTYPES.items():
                        if col in df.columns:
                            try:
                                if df[col].dtype != dtype:
                                    df[col] = df[col].astype(dtype)
                            except Exception as e:
                                print(f"   ⚠️  Warning: Failed to cast '{col}' to {dtype}: {e}")
                    
                    # Split the chunk by product and store in our dictionary
                    for product_id in df['product_id'].unique().to_pandas():
                        product_df = df[df['product_id'] == product_id].copy()
                        if product_id not in product_chunks:
                            product_chunks[product_id] = []
                        product_chunks[product_id].append(product_df)
                    
                    # Free memory after each chunk
                    del df, chunk_rows
                    cp.get_default_memory_pool().free_all_blocks()
                
                # --- WRITE STEP: WRITE CHUNKS EFFICIENTLY TO AVOID MEMORY EXHAUSTION ---
                # For large files (48M+ rows), a single concat can exhaust VRAM
                # Strategy: Write chunks iteratively, then merge if needed
                for product_id, chunks in product_chunks.items():
                    # Create partition directory
                    partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                    partition_dir.mkdir(parents=True, exist_ok=True)
                    output_file = partition_dir / "data.parquet"
                    
                    total_rows = 0
                    
                    # If only one chunk, write directly (no concat needed)
                    if len(chunks) == 1:
                        chunks[0].to_parquet(
                            output_file,
                            compression=compression,
                            index=False
                        )
                        total_rows = len(chunks[0])
                        
                        # Optionally write CSV (for Power BI compatibility)
                        if write_csv:
                            csv_file = output_file.with_suffix('.csv')
                            chunks[0].to_csv(csv_file, index=False)
                            csv_size_mb = csv_file.stat().st_size / (1024 * 1024)
                            print(f"   ✓ Wrote CSV: {csv_file.name} ({csv_size_mb:.2f} MB)")
                    else:
                        # Multiple chunks: concat in smaller batches to avoid VRAM exhaustion
                        # Strategy: concat 2-3 chunks at a time, write to temp files, then merge
                        import tempfile
                        temp_files = []
                        batch_size = 2  # Concat 2 chunks at a time (safer for memory)
                        
                        try:
                            for i in range(0, len(chunks), batch_size):
                                batch = chunks[i:i+batch_size]
                                
                                if len(batch) == 1:
                                    batch_df = batch[0]
                                else:
                                    batch_df = cudf.concat(batch, ignore_index=True)
                                
                                # Write batch to temporary file
                                temp_file = tempfile.NamedTemporaryFile(
                                    delete=False, 
                                    suffix='.parquet',
                                    dir=partition_dir
                                )
                                temp_file.close()
                                
                                batch_df.to_parquet(
                                    temp_file.name,
                                    compression=compression,
                                    index=False
                                )
                                temp_files.append(temp_file.name)
                                total_rows += len(batch_df)
                                
                                del batch_df, batch
                                cp.get_default_memory_pool().free_all_blocks()
                            
                            # Now merge all temp files into final output using PyArrow (CPU-based, memory efficient)
                            import pyarrow.parquet as pq
                            import pyarrow as pa
                            
                            # Read all temp files as PyArrow tables
                            # (print(type(tf)) for tf in temp_files)
                           
                            tables = [pq.read_table(tf) for tf in temp_files]
                            
                            # Define a unified schema to prevent dictionary encoding conflicts
                            # Force string columns to be plain strings, not dictionary-encoded
                            if tables:
                                base_schema = tables[0].schema
                                
                                # Override fields that might have inconsistent encoding
                                fixed_fields = []
                                for field in base_schema:
                                    if field.name in ['date', 'channel', 'event_type', 'product_id', 'side']:
                                        # Force to plain string (no dictionary encoding)
                                        fixed_fields.append(pa.field(field.name, pa.string()))
                                    else:
                                        # Keep original type
                                        fixed_fields.append(field)
                                
                                unified_schema = pa.schema(fixed_fields)
                                
                                # Cast all tables to the unified schema
                                tables = [table.cast(unified_schema) for table in tables]
                            
                            # Concatenate with unified schema
                            combined_table = pa.concat_tables(tables)
                            
                            # Write final Parquet table
                            pq.write_table(
                                combined_table,
                                output_file,
                                compression=compression
                            )
                            
                            # Optionally write CSV (for Power BI compatibility)
                            if write_csv:
                                import pyarrow.csv as pa_csv
                                csv_file = output_file.with_suffix('.csv')
                                pa_csv.write_csv(
                                    combined_table,
                                    csv_file,
                                    write_options=pa_csv.WriteOptions(include_header=True, delimiter=',')
                                )
                                csv_size_mb = csv_file.stat().st_size / (1024 * 1024)
                                print(f"   ✓ Wrote CSV: {csv_file.name} ({csv_size_mb:.2f} MB)")
                            
                            del tables, combined_table
                            
                        finally:
                            # Clean up temp files
                            import os
                            for tf in temp_files:
                                try:
                                    os.unlink(tf)
                                except:
                                    pass
                    
                    # Print summary
                    file_size_mb = output_file.stat().st_size / (1024 * 1024)
                    print(f"   ✓ Wrote {total_rows:,} rows for {product_id} ({file_size_mb:.2f} MB)")
                    
                    del chunks
                    cp.get_default_memory_pool().free_all_blocks()
                
                # Clean up
                del flattened_rows
                cp.get_default_memory_pool().free_all_blocks()
                    
        except Exception as e:
            print(f"   ❌ Error processing {jsonl_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        print()  # Blank line between files


def convert_ticker_data(
    input_dir: str,
    output_dir: str,
    compression: str = "snappy",
    skip_latest: bool = True,
    write_csv: bool = False
):
    """
    Convert Ticker JSONL files to Parquet format.
    Handles nested JSON structure by flattening line-by-line.
    
    Args:
        input_dir: Directory containing JSONL files
        output_dir: Directory to write Parquet files
        compression: Compression codec (snappy, gzip, zstd)
        skip_latest: If True, skip the most recent file (likely being written)
        write_csv: If True, also write CSV files alongside Parquet
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all ticker JSONL files, sorted by name
    jsonl_files = sorted(input_path.glob("ticker_*.txt"))
    
    if not jsonl_files:
        print(f"⚠️  No ticker JSONL files found in {input_dir}")
        return
    
    # Skip the latest file if requested
    if skip_latest and len(jsonl_files) > 1:
        skipped_file = jsonl_files[-1]
        jsonl_files = jsonl_files[:-1]
        print(f"⚠️  Skipping latest file (likely active): {skipped_file.name}")
    
    print(f"📁 Found {len(jsonl_files)} ticker JSONL files\n")
    
    for jsonl_file in jsonl_files:
        print(f"🔄 Processing: {jsonl_file.name}\n")
        
        # Extract date from filename
        date_str = jsonl_file.stem.split('_')[1]
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        
        monitor = GPUMemoryMonitor(f"Converting {jsonl_file.name}")
        
        try:
            with monitor:
                # Flatten nested JSON structure line-by-line
                flattened_rows = []
                
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        rows = flatten_ticker_line(line)
                        flattened_rows.extend(rows)
                
                if not flattened_rows:
                    print(f"   ⚠️  No valid data found in {jsonl_file.name}")
                    continue
                
                print(f"   ✓ Flattened {len(flattened_rows):,} ticker events from JSONL")
                
                # Process in chunks to avoid GPU OOM (5M rows at a time - smaller for ticker)
                chunk_size = 5_000_000
                product_files = {}  # Track output files per product
                
                for chunk_start in range(0, len(flattened_rows), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(flattened_rows))
                    chunk_rows = flattened_rows[chunk_start:chunk_end]
                    
                    # Convert chunk to cuDF DataFrame
                    df = cudf.DataFrame(chunk_rows)
                    
                    # Add date column for partitioning
                    df['date'] = date
                    
                    # Convert timestamps to datetime (handle mixed formats)
                    import pandas as pd
                    df_timestamp = df['timestamp'].to_pandas()
                    df['timestamp'] = cudf.from_pandas(pd.to_datetime(df_timestamp, format='mixed', utc=True))
                    
                    # Convert numeric columns
                    numeric_cols = [
                        'price', 'volume_24_h', 'low_24_h', 'high_24_h', 
                        'low_52_w', 'high_52_w', 'price_percent_chg_24_h',
                        'best_bid', 'best_ask', 'best_bid_quantity', 'best_ask_quantity'
                    ]
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(float)
                    
                    df['sequence_num'] = df['sequence_num'].astype(int)
                    
                    # Write to Parquet with partitioning by date and product
                    for product_id in df['product_id'].unique().to_pandas():
                        product_df = df[df['product_id'] == product_id]
                        
                        # Create partition directory
                        partition_dir = output_path / f"date={date}" / f"product_id={product_id}"
                        partition_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Write Parquet file (append mode if file exists from THIS run)
                        output_file = partition_dir / "data.parquet"
                        
                        # Check if file exists AND was created in this chunking loop
                        if output_file.exists() and product_id in product_files:
                            # Append to existing file (safe - same schema)
                            existing_df = cudf.read_parquet(output_file)
                            combined_df = cudf.concat([existing_df, product_df], ignore_index=True)
                            combined_df.to_parquet(
                                output_file,
                                compression=compression,
                                index=False
                            )
                            del existing_df, combined_df
                        else:
                            # Create new file or overwrite old one
                            product_df.to_parquet(
                                output_file,
                                compression=compression,
                                index=False
                            )
                        
                        # Track file for summary
                        if product_id not in product_files:
                            product_files[product_id] = {'rows': 0, 'file': output_file}
                        product_files[product_id]['rows'] += len(product_df)
                    
                    # Free memory after each chunk
                    del df
                    cp.get_default_memory_pool().free_all_blocks()
                
                # Print summary
                for product_id, info in product_files.items():
                    file_size_mb = info['file'].stat().st_size / (1024 * 1024)
                    print(f"   ✓ Wrote {info['rows']:,} rows for {product_id} ({file_size_mb:.2f} MB)")
                    
                    # Optionally write CSV (for Power BI compatibility)
                    if write_csv:
                        csv_file = info['file'].with_suffix('.csv')
                        # Read Parquet and write CSV (memory-efficient via PyArrow)
                        import pyarrow.parquet as pq
                        import pyarrow.csv as pa_csv
                        table = pq.read_table(info['file'])
                        pa_csv.write_csv(
                            table,
                            csv_file,
                            write_options=pa_csv.WriteOptions(include_header=True, delimiter=',')
                        )
                        csv_size_mb = csv_file.stat().st_size / (1024 * 1024)
                        print(f"   ✓ Wrote CSV: {csv_file.name} ({csv_size_mb:.2f} MB)")
                
                # Clean up
                del flattened_rows
                cp.get_default_memory_pool().free_all_blocks()
                    
        except Exception as e:
            print(f"   ❌ Error processing {jsonl_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        print()  # Blank line between files


def validate_conversion(parquet_dir: str):
    """
    Validate converted Parquet files.
    
    Args:
        parquet_dir: Directory containing Parquet files
    """
    print("="*60)
    print("📊 CONVERSION VALIDATION")
    print("="*60)
    print()
    
    parquet_path = Path(parquet_dir)
    
    # Check Level2 data
    level2_dir = parquet_path / "level2"
    if level2_dir.exists():
        level2_files = list(level2_dir.rglob("*.parquet"))
        print(f"📁 Level2 Data:")
        print(f"   Files: {len(level2_files)}")
        
        if level2_files:
            # Count total rows
            total_rows = 0
            total_size = 0
            for file in level2_files:
                df = cudf.read_parquet(file)
                total_rows += len(df)
                total_size += file.stat().st_size
            
            print(f"   Total Rows: {total_rows:,}")
            print(f"   Total Size: {total_size / (1024**2):.2f} MB")
            print(f"   Avg File Size: {total_size / len(level2_files) / (1024**2):.2f} MB")
    else:
        print("📁 Level2 Data: Not found")
    
    print()
    
    # Check Ticker data
    ticker_dir = parquet_path / "ticker"
    if ticker_dir.exists():
        ticker_files = list(ticker_dir.rglob("*.parquet"))
        print(f"📁 Ticker Data:")
        print(f"   Files: {len(ticker_files)}")
        
        if ticker_files:
            total_rows = 0
            total_size = 0
            for file in ticker_files:
                df = cudf.read_parquet(file)
                total_rows += len(df)
                total_size += file.stat().st_size
            
            print(f"   Total Rows: {total_rows:,}")
            print(f"   Total Size: {total_size / (1024**2):.2f} MB")
            print(f"   Avg File Size: {total_size / len(ticker_files) / (1024**2):.2f} MB")
    else:
        print("📁 Ticker Data: Not found")
    
    print()
    print("✅ Validation complete!")


def main():
    """Main entry point for JSONL → Parquet conversion."""
    parser = argparse.ArgumentParser(
        description="Convert JSONL websocket data to Parquet format (GPU-accelerated)"
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
        "--include-latest",
        action="store_true",
        help="Include the latest file (risky if collector is running)"
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
    
    # Calculate skip_latest (opposite of include_latest)
    skip_latest = not args.include_latest
    
    # Validation mode
    if args.validate:
        validate_conversion(str(PARQUET_LEVEL2_DIR.parent))
        return
    
    # Print header
    print("="*60)
    print("🚀 JSONL → Parquet Conversion (GPU-Accelerated)")
    print("="*60)
    print(f"Input:  {args.input_dir}")
    print(f"Output: {PARQUET_LEVEL2_DIR.parent}")
    print(f"Compression: {args.compression}")
    print("="*60)
    print()
    
    # Convert Level2 data
    print("📦 Converting Level2 data...")
    if args.write_csv:
        print("📄 CSV export enabled")
    convert_level2_data(
        input_dir=args.input_dir,
        output_dir=str(PARQUET_LEVEL2_DIR),
        compression=args.compression,
        skip_latest=skip_latest,
        write_csv=args.write_csv
    )
    
    print("\n" + "="*60 + "\n")
    
    # Convert Ticker data
    print("📦 Converting Ticker data...")
    convert_ticker_data(
        input_dir=args.input_dir,
        output_dir=str(PARQUET_TICKER_DIR),
        compression=args.compression,
        skip_latest=skip_latest,
        write_csv=args.write_csv
    )
    
    print("\n" + "="*60)
    print()
    
    # Validate conversion
    validate_conversion(str(PARQUET_LEVEL2_DIR.parent))
    
    print("\n" + "="*60)
    print("🎉 ALL DONE!")
    print("="*60)
    print()
    print("Next steps:")
    print(f"1. Check output: ls {PARQUET_LEVEL2_DIR.parent}")
    print("2. Run Stage 2: python gpu/stage2_orderbook_builder.py")
    print("3. See QUICKSTART.md for detailed usage")


if __name__ == "__main__":
    main()

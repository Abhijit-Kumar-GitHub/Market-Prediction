#!/usr/bin/env python3
"""
Stage 0: CSV to Parquet Conversion (GPU-Accelerated)

One-time conversion of existing CSV data to optimized Parquet format.
This enables 5-10x compression, 10-20x faster loading, and partition pruning.

Usage:
    python src/data/converters/csv_to_parquet.py
    python src/data/converters/csv_to_parquet.py --input datasets/raw_csv --output datasets/parquet
"""

import argparse
import cudf
import cupy as cp
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.gpu_config import (
    RAW_CSV_DIR, PARQUET_DIR, PARQUET_LEVEL2_DIR, PARQUET_TICKER_DIR,
    COMPRESSION, LEVEL2_PARTITION_COLS, TICKER_PARTITION_COLS
)
from src.utils.parquet_utils import ParquetManager, csv_to_parquet_batch
from src.utils.gpu_memory import GPUMemoryMonitor, print_gpu_info


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert CSV data to Parquet format (GPU-accelerated)'
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        default=RAW_CSV_DIR,
        help=f'Input directory with CSV files (default: {RAW_CSV_DIR})'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=PARQUET_DIR,
        help=f'Output directory for Parquet files (default: {PARQUET_DIR})'
    )
    
    parser.add_argument(
        '--compression',
        choices=['snappy', 'gzip', 'zstd'],
        default=COMPRESSION,
        help=f'Compression codec (default: {COMPRESSION})'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=10_000_000,
        help='Rows to process at once (default: 10M)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate output after conversion'
    )
    
    return parser.parse_args()


def convert_level2_data(input_dir: Path, output_dir: Path, 
                        compression: str, chunk_size: int) -> None:
    """
    Convert Level2 CSV files to Parquet.
    
    Args:
        input_dir: Directory with level2_*.csv files
        output_dir: Output directory
        compression: Compression codec
        chunk_size: Rows per chunk
    """
    print("\n" + "=" * 80)
    print("CONVERTING LEVEL2 DATA (Order Book Events)")
    print("=" * 80)
    
    # Find all level2 CSV files
    csv_files = sorted(input_dir.glob('level2_*.csv'))
    
    if not csv_files:
        print(f"No level2_*.csv files found in {input_dir}")
        return
    
    print(f"\nFound {len(csv_files)} Level2 CSV files:")
    for f in csv_files:
        size_mb = f.stat().st_size / 1024**2
        print(f"   - {f.name} ({size_mb:.1f} MB)")
    
    # Convert with GPU acceleration
    level2_output = output_dir / 'level2'
    level2_output.mkdir(parents=True, exist_ok=True)
    
    with GPUMemoryMonitor("Level2 CSV → Parquet"):
        csv_to_parquet_batch(
            csv_files=csv_files,
            output_dir=level2_output,
            partition_cols=LEVEL2_PARTITION_COLS,
            compression=compression,
            chunk_size=chunk_size
        )
    
    print("\nLevel2 conversion complete!")


def convert_ticker_data(input_dir: Path, output_dir: Path,
                        compression: str, chunk_size: int) -> None:
    """
    Convert Ticker CSV files to Parquet.
    
    Args:
        input_dir: Directory with ticker_*.csv files
        output_dir: Output directory
        compression: Compression codec
        chunk_size: Rows per chunk
    """
    print("\n" + "=" * 80)
    print("CONVERTING TICKER DATA (Market Snapshots)")
    print("=" * 80)
    
    # Find all ticker CSV files
    csv_files = sorted(input_dir.glob('ticker_*.csv'))
    
    if not csv_files:
        print(f"No ticker_*.csv files found in {input_dir}")
        return
    
    print(f"\nFound {len(csv_files)} Ticker CSV files:")
    for f in csv_files:
        size_mb = f.stat().st_size / 1024**2
        print(f"   - {f.name} ({size_mb:.1f} MB)")
    
    # Convert with GPU acceleration
    ticker_output = output_dir / 'ticker'
    ticker_output.mkdir(parents=True, exist_ok=True)
    
    with GPUMemoryMonitor("Ticker CSV → Parquet"):
        csv_to_parquet_batch(
            csv_files=csv_files,
            output_dir=ticker_output,
            partition_cols=TICKER_PARTITION_COLS,
            compression=compression,
            chunk_size=chunk_size
        )
    
    print("\nTicker conversion complete!")


def validate_conversion(output_dir: Path) -> None:
    """
    Validate converted Parquet files.
    
    Args:
        output_dir: Directory with Parquet files
    """
    print("\n" + "=" * 80)
    print("VALIDATING CONVERSION")
    print("=" * 80)
    
    # Level2 validation
    print("\n1. Level2 validation:")
    level2_manager = ParquetManager(output_dir / 'level2')
    level2_stats = level2_manager.get_statistics()
    
    print(f"   Files: {level2_stats['num_files']}")
    print(f"   Size: {level2_stats['total_size_mb']:.1f} MB")
    print(f"   Dates: {level2_stats['num_dates']} days")
    print(f"   Products: {', '.join(level2_stats['products'])}")
    
    # Read sample to verify
    if level2_stats['dates']:
        sample_date = level2_stats['dates'][0]
        sample_df = level2_manager.read_date(sample_date)
        print(f"   Sample read: {len(sample_df):,} rows from {sample_date}")
        print(f"   Columns: {list(sample_df.columns)}")
    
    # Ticker validation
    print("\n2. Ticker validation:")
    ticker_manager = ParquetManager(output_dir / 'ticker')
    ticker_stats = ticker_manager.get_statistics()
    
    print(f"   Files: {ticker_stats['num_files']}")
    print(f"   Size: {ticker_stats['total_size_mb']:.1f} MB")
    print(f"   Dates: {ticker_stats['num_dates']} days")
    
    if ticker_stats['dates']:
        sample_date = ticker_stats['dates'][0]
        sample_df = ticker_manager.read_date(sample_date)
        print(f"   Sample read: {len(sample_df):,} rows from {sample_date}")
        print(f"   Columns: {list(sample_df.columns)}")
    
    # Calculate compression ratio
    print("\n3. Compression analysis:")
    
    # Get original CSV size
    csv_size_mb = sum(
        f.stat().st_size for f in (output_dir.parent.parent / 'raw_csv').glob('*.csv')
    ) / 1024**2 if (output_dir.parent.parent / 'raw_csv').exists() else 0
    
    parquet_size_mb = level2_stats['total_size_mb'] + ticker_stats['total_size_mb']
    
    if csv_size_mb > 0:
        compression_ratio = csv_size_mb / parquet_size_mb
        print(f"   CSV size:     {csv_size_mb:.1f} MB")
        print(f"   Parquet size: {parquet_size_mb:.1f} MB")
        print(f"   Compression:  {compression_ratio:.1f}x")
        print(f"   Savings:      {csv_size_mb - parquet_size_mb:.1f} MB ({(1-parquet_size_mb/csv_size_mb)*100:.1f}%)")
    
    print("\nValidation complete!")


def main():
    """Main conversion pipeline."""
    args = parse_args()
    
    print("=" * 80)
    print("CSV → PARQUET CONVERSION (GPU-ACCELERATED)")
    print("=" * 80)
    print(f"\nInput:       {args.input}")
    print(f"Output:      {args.output}")
    print(f"Compression: {args.compression}")
    print(f"Chunk size:  {args.chunk_size:,} rows")
    
    # Show GPU info
    print_gpu_info()
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Convert Level2 data
    convert_level2_data(
        input_dir=args.input,
        output_dir=args.output,
        compression=args.compression,
        chunk_size=args.chunk_size
    )
    
    # Convert Ticker data
    convert_ticker_data(
        input_dir=args.input,
        output_dir=args.output,
        compression=args.compression,
        chunk_size=args.chunk_size
    )
    
    # Validate if requested
    if args.validate:
        validate_conversion(args.output)
    
    # Final summary
    print("\n" + "=" * 80)
    print("CONVERSION COMPLETE!")
    print("=" * 80)
    
    print("\nNext steps:")
    print("   1. Run Stage 2: python gpu/stage2_orderbook_gpu.py")
    print("   2. Run Stage 3: python gpu/stage3_features_gpu.py")
    print("   3. Train models: python gpu/stage4_ml_training_gpu.py")
    
    print("\nTips:")
    print("   - Use partition pruning: read_parquet(..., filters=[('date', '>=', '2025-11-01')])")
    print("   - Load only needed columns: read_parquet(..., columns=['timestamp', 'price'])")
    print("   - Process day-by-day to avoid OOM")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

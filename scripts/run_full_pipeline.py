"""
QUICK START: Run the entire pipeline
====================================

This script runs all 3 stages in sequence.
Perfect for demos or after getting new data.

Usage:
    python run_full_pipeline.py

Expected runtime on NVIDIA DGX-A100:
- Stage 1: ~2 minutes (JSONL → CSV)
- Stage 2: ~15 minutes (48M events → 17K snapshots)
- Stage 3: ~30 seconds (feature engineering)

Total: ~20 minutes for complete pipeline
"""

import subprocess
import sys
from pathlib import Path
import time

def run_stage(stage_num, script_name, description):
    """Run a pipeline stage and track timing"""
    print("\n" + "="*80)
    print(f"STAGE {stage_num}: {description}")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, f"data_pipeline/{script_name}"],
            check=True,
            capture_output=False
        )
        
        elapsed = time.time() - start_time
        print(f"\nStage {stage_num} completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\nStage {stage_num} failed with error code {e.returncode}")
        return False

def main():
    """Execute full pipeline"""
    
    print("\n" + "="*80)
    print("FULL PIPELINE EXECUTION")
    print("="*80)
    print("\nThis will run GPU-accelerated pipeline:")
    print("  Stage 0: JSONL → Parquet conversion")
    print("  Stage 1: Data quality verification.")
    print("  Stage 2: Order book reconstruction")
    print("  Stage 3: Feature engineering.")
    print("  Stage 4 ...")
    print("\nEstimated time: ~20 minutes on NVIDIA DGX-A100")
    print("="*80 + "\n")
    
    # Confirm
    response = input("Continue? [Y/n]: ")
    if response.lower() not in ['', 'y', 'yes']:
        print("Aborted.")
        return
    
    pipeline_start = time.time()
    
    # Stage 0: JSONL → Parquet (GPU)
    print("\n" + "="*80)
    print(f"STAGE 0: JSONL → Parquet Conversion (GPU)")
    print("="*80 + "\n")
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "src/data/converters/jsonl_to_parquet.py"],
            check=True,
            capture_output=False
        )
        elapsed = time.time() - start_time
        print(f"\nStage 0 completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    except subprocess.CalledProcessError as e:
        print(f"\nStage 0 failed with error code {e.returncode}")
        print("\nPipeline aborted at Stage 0")
        return
    
    # Stage 2: Order Book Reconstruction
    if not run_stage(2, "stage2_orderbook_builder.py", "Order Book Reconstruction"):
        print("\nPipeline aborted at Stage 2")
        return
    
    # Stage 3: ML Features
    if not run_stage(3, "stage3_ml_features.py", "ML Feature Engineering"):
        print("\nPipeline aborted at Stage 3")
        return
    
    # Success!
    total_time = time.time() - pipeline_start
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETE!")
    print("="*80)
    print(f"\nTotal runtime: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("\nOutput files:")
    print("  - datasets/raw_csv/level2_*.csv")
    print("  - datasets/raw_csv/ticker_*.csv")
    print("  - datasets/market_snapshots.csv")
    print("  - datasets/crypto_features.csv")
    print("\nReady for ML modeling!")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()

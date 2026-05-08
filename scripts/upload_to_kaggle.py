#!/usr/bin/env python3
"""
Upload datasets to Kaggle using .env credentials

Two datasets:
1. Parquet data  - uploaded once, reused
2. Code (notebooks, src, scripts) - updated as needed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import subprocess

# Load credentials from .env
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# Set Kaggle environment variables
os.environ['KAGGLE_USERNAME'] = os.getenv('KAGGLE_USERNAME')
os.environ['KAGGLE_KEY'] = os.getenv('KAGGLE_KEY')

def upload_dataset(dataset_path, dataset_type):
    """Upload or update a Kaggle dataset"""
    print("=" * 60)
    print(f"Uploading {dataset_type}")
    print("=" * 60)
    print(f"Path: {dataset_path}")
    print(f"Username: {os.environ['KAGGLE_USERNAME']}")
    print()
    
    # Create new dataset
    print(f"Running: kaggle datasets create -p {dataset_path}")
    result = subprocess.run(
        ['kaggle', 'datasets', 'create', '-p', str(dataset_path)],
        capture_output=True,
        text=True
    )
    
    # Always show output for debugging
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    if result.returncode == 0:
        print(f"✓ {dataset_type} upload successful!")
    else:
        # If dataset exists, create new version
        if result.stderr and "already exists" in result.stderr.lower():
            print(f"\n{dataset_type} exists, creating new version...")
            result = subprocess.run(
                ['kaggle', 'datasets', 'version', '-p', str(dataset_path), '-m', 'Updated'],
                capture_output=True,
                text=True
            )
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            
            if result.returncode == 0:
                print(f"✓ {dataset_type} version update successful!")
            else:
                print(f"✗ Error updating {dataset_type}")
                return False
        else:
            print(f"✗ Error uploading {dataset_type}")
            return False
    
    return True

if __name__ == "__main__":
    upload_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if upload_type in ["all", "data"]:
        # Upload parquet data
        parquet_dir = project_root / 'datasets' / 'parquet'
        level2_files = list((parquet_dir / 'level2').rglob('*.parquet'))
        ticker_files = list((parquet_dir / 'ticker').rglob('*.parquet'))
        total_size_mb = sum(f.stat().st_size for f in level2_files + ticker_files) / (1024**2)
        
        print(f"Level2 files: {len(level2_files)}")
        print(f"Ticker files: {len(ticker_files)}")
        print(f"Total size: {total_size_mb:.1f} MB ({total_size_mb/1024:.2f} GB)")
        print()
        
        if not upload_dataset(parquet_dir, "PARQUET DATA"):
            sys.exit(1)
        print()
    
    if upload_type in ["all", "code"]:
        # Upload code (notebooks, src, scripts)
        code_dir = project_root
        
        # Count files that will be uploaded
        notebooks = list(code_dir.glob('notebooks/*.ipynb'))
        src_files = list((code_dir / 'src').rglob('*.py'))
        scripts = list((code_dir / 'scripts').rglob('*.py'))
        
        print(f"Notebooks: {len(notebooks)}")
        print(f"Source files: {len(src_files)}")
        print(f"Scripts: {len(scripts)}")
        print()
        
        if not upload_dataset(code_dir, "CODE"):
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print("\nOn Kaggle:")
    print("1. Create a new notebook")
    print("2. Add Input > Add dataset > Search for your datasets")
    print("3. Data will be at: /kaggle/input/crypto-dataset-parquet/")
    print("4. Code will be at: /kaggle/input/crypto-orderbook-ml-code/")
    print("=" * 60)

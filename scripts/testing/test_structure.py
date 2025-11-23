#!/usr/bin/env python3
"""
Test script to verify project structure and imports (CPU-only, no GPU required)
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing Project Structure\n")
    print("="*60)
    
    # Test 1: Config import
    print("\n[Test 1] Testing config import...")
    try:
        from config.gpu_config import (
            JSONL_INPUT_DIR, 
            PARQUET_LEVEL2_DIR,
            COMPRESSION
        )
        print(f"✅ Config imported successfully")
        print(f"   JSONL_INPUT_DIR: {JSONL_INPUT_DIR}")
        print(f"   PARQUET_LEVEL2_DIR: {PARQUET_LEVEL2_DIR}")
        print(f"   COMPRESSION: {COMPRESSION}")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    # Test 2: Collector import
    print("\n[Test 2] Testing collector import...")
    try:
        from src.data.collector import CryptoDataCollector
        print(f"✅ Collector imported successfully")
        print(f"   Class: {CryptoDataCollector.__name__}")
    except Exception as e:
        print(f"❌ Collector import failed: {e}")
        return False
    
    # Test 3: Check utilities files exist (don't import due to cudf dependency)
    print("\n[Test 3] Checking utility files exist...")
    util_files = [
        "src/utils/parquet_utils.py",
        "src/utils/gpu_memory.py",
        "src/utils/__init__.py"
    ]
    for util_file in util_files:
        if Path(util_file).exists():
            print(f"✅ Found: {util_file}")
        else:
            print(f"❌ Missing: {util_file}")
            return False
    
    # Test 4: Check GPU utilities exist (but don't import cudf)
    print("\n[Test 4] Checking GPU utility files exist...")
    gpu_mem_path = Path("src/utils/gpu_memory.py")
    if gpu_mem_path.exists():
        print(f"✅ GPU utilities found: {gpu_mem_path}")
    else:
        print(f"❌ GPU utilities not found: {gpu_mem_path}")
        return False
    
    # Test 5: Check converter scripts exist
    print("\n[Test 5] Checking converter scripts exist...")
    converter_scripts = [
        "src/data/converters/jsonl_to_parquet.py",
        "src/data/converters/csv_to_parquet.py"
    ]
    for script in converter_scripts:
        if Path(script).exists():
            print(f"✅ Found: {script}")
        else:
            print(f"❌ Missing: {script}")
            return False
    
    # Test 6: Check archive structure
    print("\n[Test 6] Checking archive structure...")
    archive_dirs = [
        "_archive_old_structure/old_docs",
        "_archive_old_structure/old_scripts",
        "_archive_old_structure/old_data"
    ]
    for dir_path in archive_dirs:
        if Path(dir_path).exists():
            count = len(list(Path(dir_path).iterdir()))
            print(f"✅ Archive exists: {dir_path} ({count} items)")
        else:
            print(f"❌ Archive missing: {dir_path}")
            return False
    
    print("\n" + "="*60)
    print("🎉 All tests passed! Project structure is valid.")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)

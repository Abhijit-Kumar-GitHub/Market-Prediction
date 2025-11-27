#!/usr/bin/env python3
"""
Verification script to check all paths and imports after restructure.
Run this before Week 1 to ensure everything is properly configured.

Usage:
    python scripts/testing/verify_paths.py
"""

import sys
import os
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def test_import(module_path, description):
    """Test if a module can be imported"""
    try:
        exec(f"import {module_path}")
        print(f"{GREEN}✓{RESET} {description}: {module_path}")
        return True
    except ImportError as e:
        print(f"{RED}✗{RESET} {description}: {module_path}")
        print(f"  Error: {e}")
        return False
    except Exception as e:
        print(f"{YELLOW}⚠{RESET} {description}: {module_path}")
        print(f"  Unexpected error: {type(e).__name__}: {e}")
        return False

def test_file_exists(file_path, description):
    """Test if a file exists"""
    path = Path(file_path)
    if path.exists():
        print(f"{GREEN}✓{RESET} {description}: {file_path}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {file_path}")
        print(f"  File not found")
        return False

def main():
    print("=" * 70)
    print("PATH & IMPORT VERIFICATION - Post-Restructure")
    print("=" * 70)
    print()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    print(f"Project Root: {project_root}")
    print()
    
    # Track results
    tests_passed = 0
    tests_failed = 0
    
    # ========================================
    print("Testing Config Imports")
    print("-" * 70)
    
    if test_import("config.gpu_config", "GPU Config"):
        tests_passed += 1
        
        # Try to access specific config variables
        try:
            from config.gpu_config import JSONL_INPUT_DIR, PARQUET_DIR, PROJECT_ROOT
            print(f"    JSONL_INPUT_DIR: {JSONL_INPUT_DIR}")
            print(f"    PARQUET_DIR: {PARQUET_DIR}")
            print(f"    PROJECT_ROOT: {PROJECT_ROOT}")
            tests_passed += 1
        except ImportError as e:
            print(f"{YELLOW}{RESET} Could not import config variables: {e}")
            tests_failed += 1
    else:
        tests_failed += 1
    
    print()
    
    # ========================================
    print("Testing Utils Imports")
    print("-" * 70)
    
    if test_import("src.utils.gpu_memory", "GPU Memory Utils"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_import("src.utils.parquet_utils", "Parquet Utils"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # ========================================
    print("Testing Critical Files Exist")
    print("-" * 70)
    
    critical_files = [
        ("src/data/collector.py", "Data Collector"),
        ("src/data/converters/jsonl_to_parquet.py", "JSONL Converter"),
        ("src/data/converters/csv_to_parquet.py", "CSV Converter"),
        ("config/gpu_config.py", "GPU Config"),
        ("scripts/run_collector_24x7.py", "Collector Runner"),
        ("todo.txt", "Todo List"),
        ("README.md", "README"),
        ("CHANGELOG.md", "Changelog")
    ]
    
    for file_path, description in critical_files:
        if test_file_exists(project_root / file_path, description):
            tests_passed += 1
        else:
            tests_failed += 1
    
    print()
    
    # ========================================
    print("Testing Directory Structure")
    print("-" * 70)
    
    critical_dirs = [
        ("src/data", "Data Module"),
        ("src/data/converters", "Converters"),
        ("src/utils", "Utils"),
        ("src/preprocessing", "Preprocessing (empty OK)"),
        ("src/models", "Models (empty OK)"),
        ("config", "Config"),
        ("scripts", "Scripts"),
        ("docs", "Documentation"),
        ("outputs", "Outputs (may not exist yet)"),
        ("outputs/logs", "Logs (may not exist yet)"),
        ("outputs/models", "Models Output (may not exist yet)"),
        ("outputs/plots", "Plots Output (may not exist yet)"),
        ("crypto_data_jsonl", "JSONL Data (may not exist yet)")
    ]
    
    for dir_path, description in critical_dirs:
        path = project_root / dir_path
        if path.exists():
            print(f"{GREEN}✓{RESET} {description}: {dir_path}")
            tests_passed += 1
        else:
            if "may not exist" in description:
                print(f"{YELLOW}⚠{RESET} {description}: {dir_path} (not created yet)")
            else:
                print(f"{RED}✗{RESET} {description}: {dir_path} (MISSING)")
                tests_failed += 1
    
    print()
    
    # ========================================
    print("Checking for Old Path References")
    print("-" * 70)
    
    # Search for old 'gpu.' imports in src/
    import subprocess
    
    try:
        result = subprocess.run(
            ['grep', '-r', 'from gpu\\.', 'src/', '--include=*.py'],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0 and result.stdout:
            print(f"{RED}✗{RESET} Found old 'gpu.' imports in src/:")
            print(result.stdout)
            tests_failed += 1
        else:
            print(f"{GREEN}✓{RESET} No old 'gpu.' imports found in src/")
            tests_passed += 1
    except FileNotFoundError:
        # grep not available (Windows without Git Bash)
        print(f"{YELLOW}⚠{RESET} grep not available, skipping old path search")
        print("  Manually check for 'from gpu.' or 'import gpu.' in src/ files")
    
    print()
    
    # ========================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{GREEN}Passed:{RESET} {tests_passed}")
    print(f"{RED}Failed:{RESET} {tests_failed}")
    print()
    
    if tests_failed == 0:
        print(f"{GREEN}ALL TESTS PASSED!{RESET}")
        print("Project structure is ready for Week 1")
        return 0
    else:
        print(f"{RED}SOME TESTS FAILED{RESET}")
        print("Fix these issues before starting Week 1")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

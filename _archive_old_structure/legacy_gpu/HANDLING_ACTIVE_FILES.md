# Handling Active Files in Data Pipeline

## Problem Statement

**Scenario:** You have a data collector running 24/7 that writes to:
- `crypto_data_jsonl/level2_20251114.txt` (currently being written)
- `crypto_data_jsonl/ticker_20251114.txt` (currently being written)

**Issue:** If the converter tries to read these files while the collector is writing, you get:

### 1. **Race Conditions**
```
Collector: Writing line 50,000
Converter: Reading line 50,000 ← File changes mid-read!
Result: Corrupted data or incomplete JSON
```

### 2. **Incomplete JSON Lines**
```jsonl
{"type":"l2update","product_id":"BTC-USD","time":"2025-11-14T12:00:00Z"}
{"type":"l2update","product_id":"BTC-USD","ti   ← INCOMPLETE!
```
**Result:** `JSONDecodeError: Unterminated string`

### 3. **File Locks (Windows)**
- Collector has file open for writing
- Converter tries to open for reading
- **Result:** Permission denied or corrupted reads

---

## ✅ Solution Implemented

### **Default Behavior: Skip Latest File**

The converter now **automatically skips the most recent file** (which is likely still being written):

```bash
# By default, skips the latest file
python gpu/stage0_jsonl_to_parquet.py

# Output:
⚠️  Skipping latest file (likely active): level2_20251114.txt
⚠️  Skipping latest file (likely active): ticker_20251114.txt

📁 Found 2 level2 JSONL files
🔄 Processing: level2_20251107.txt ✓
🔄 Processing: level2_20251108.txt ✓

# level2_20251114.txt is NOT converted (still being written)
```

### **Override: Include Latest File (Risky)**

If you're **sure** the collector is stopped:

```bash
# Include all files (use with caution!)
python gpu/stage0_jsonl_to_parquet.py --include-latest
```

---

## 📋 Recommended Workflow

### **Option 1: Daily Batch Conversion (RECOMMENDED)**

Run conversion once per day for **completed files only**:

```bash
# Cron job at 00:05 (5 minutes after midnight)
# Converts yesterday's completed files
0 5 0 * * * cd ~/MarketPrediction && python gpu/stage0_jsonl_to_parquet.py
```

**How it works:**
- **Nov 13, 11:59 PM:** Collector writes to `level2_20251113.txt`
- **Nov 14, 12:00 AM:** Collector rotates to `level2_20251114.txt` (new file)
- **Nov 14, 12:05 AM:** Converter runs, processes `level2_20251113.txt` (complete!)
- **Nov 14, 12:05 AM:** Skips `level2_20251114.txt` (still being written)

**Benefits:**
- ✅ Never reads active files
- ✅ Processes complete days only
- ✅ Automated, hands-off

---

### **Option 2: Stop Collector Before Conversion**

Manually stop collector, convert all files, restart:

```bash
# 1. Stop collector
pkill -f run_collector_24x7.py

# 2. Convert ALL files (including latest)
python gpu/stage0_jsonl_to_parquet.py --include-latest

# 3. Restart collector
nohup python run_collector_24x7.py &
```

**Use case:** One-time migration, backfilling historical data

---

### **Option 3: File Rotation Strategy**

Modify collector to rotate files more frequently:

**Current (daily rotation):**
```
level2_20251114.txt  ← All day's data (500M+ events, risky)
```

**Improved (hourly rotation):**
```
level2_20251114_00.txt  ← 00:00-00:59 (complete)
level2_20251114_01.txt  ← 01:00-01:59 (complete)
...
level2_20251114_23.txt  ← 23:00-23:59 (currently writing)
```

**Benefits:**
- ✅ Smaller files (easier to handle)
- ✅ Convert completed hours while collector runs
- ✅ Max 1 hour of data at risk

**Implementation:**
```python
# In your collector script
from datetime import datetime

# Generate filename with hour
now = datetime.now()
filename = f"level2_{now:%Y%m%d_%H}.txt"  # level2_20251114_15.txt

# Rotate every hour
if now.minute == 0:
    file_handle.close()
    file_handle = open(new_filename, 'a')
```

---

## 🔍 Detection: Is File Currently Active?

**Method 1: File Age**
```python
from datetime import datetime, timedelta
from pathlib import Path

def is_file_active(filepath: Path, max_age_minutes: int = 60) -> bool:
    """Check if file was modified recently (likely still being written)."""
    if not filepath.exists():
        return False
    
    file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    age = datetime.now() - file_mtime
    
    return age < timedelta(minutes=max_age_minutes)

# Example
if is_file_active(Path("crypto_data_jsonl/level2_20251114.txt")):
    print("⚠️  File is likely active, skipping...")
```

**Method 2: File Lock Check (Windows)**
```python
import os

def is_file_locked(filepath: str) -> bool:
    """Check if file is currently locked by another process."""
    try:
        # Try to rename file to itself (doesn't actually rename)
        os.rename(filepath, filepath)
        return False  # Not locked
    except OSError:
        return True  # Locked by another process
```

**Method 3: Process Check**
```python
import psutil

def is_collector_running() -> bool:
    """Check if data collector process is running."""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'run_collector_24x7.py' in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

# Example
if is_collector_running():
    print("⚠️  Collector is running, using --skip-latest")
```

---

## 🛡️ Error Handling

The converter now has robust error handling:

```python
try:
    df = cudf.read_json(file, lines=True)
except Exception as e:
    if "JSONDecodeError" in str(e):
        print(f"⚠️  Incomplete JSON in {file.name}, likely still being written")
        print(f"   Skipping this file. Run again later with --include-latest")
    else:
        print(f"❌ Error: {e}")
    continue  # Skip to next file
```

**Benefits:**
- ✅ Doesn't crash on incomplete JSON
- ✅ Logs warning and continues
- ✅ Can retry later

---

## 📊 Summary Table

| Approach | Safety | Automation | Data Loss Risk | Complexity |
|----------|--------|------------|----------------|------------|
| **Skip latest (default)** | ✅ High | ✅ Yes | ⚠️ Max 1 day | ⭐ Low |
| **Stop collector** | ✅ High | ❌ Manual | ✅ None | ⭐⭐ Medium |
| **Hourly rotation** | ✅ High | ✅ Yes | ⚠️ Max 1 hour | ⭐⭐⭐ High |
| **Include latest (risky)** | ❌ Low | ✅ Yes | 🚨 High | ⭐ Low |

---

## 🎯 Recommended Setup

**For production:**

1. **Collector rotates files daily** (at midnight)
   ```python
   filename = f"level2_{datetime.now():%Y%m%d}.txt"
   ```

2. **Converter runs daily at 00:05** (5 min after midnight)
   ```bash
   # Cron job
   5 0 * * * cd ~/MarketPrediction && python gpu/stage0_jsonl_to_parquet.py
   ```

3. **Default behavior: Skip latest file**
   - Converts yesterday's complete file
   - Skips today's active file
   - Max data lag: 1 day

4. **Monitor for errors**
   ```bash
   # Log output
   python gpu/stage0_jsonl_to_parquet.py >> logs/conversion.log 2>&1
   
   # Check for errors
   grep "Error" logs/conversion.log
   ```

---

## 🚀 Usage Examples

```bash
# Standard daily run (safe, automated)
python gpu/stage0_jsonl_to_parquet.py

# Convert only level2 data (skip ticker)
python gpu/stage0_jsonl_to_parquet.py --level2-only

# Use ZSTD compression (best compression, slower)
python gpu/stage0_jsonl_to_parquet.py --compression zstd

# Include latest file (ONLY if collector is stopped!)
python gpu/stage0_jsonl_to_parquet.py --include-latest

# Validate existing Parquet files
python gpu/stage0_jsonl_to_parquet.py --validate
```

---

## 📝 Interview Talking Point

> "I encountered a concurrency issue where my data collector writes to JSONL files 24/7, but the converter needs to read them. Reading an actively-written file causes race conditions and incomplete JSON parsing.
>
> I implemented a **skip-latest-file strategy**: the converter automatically skips the most recent file (which is likely still being written) and only processes complete files. Combined with daily cron scheduling at midnight, this ensures we only convert yesterday's complete data.
>
> For better granularity, I also designed an **hourly rotation strategy** where the collector creates new files every hour, reducing the max data lag from 24 hours to 1 hour while maintaining safety."

---

## ✅ Verification

**Test that skip-latest works:**

```bash
# List your JSONL files
ls -lh crypto_data_jsonl/

# Output:
# level2_20251107.txt  (10 GB, old)
# level2_20251108.txt  (10 GB, old)
# level2_20251114.txt  (5 GB, recent ← ACTIVE)

# Run converter
python gpu/stage0_jsonl_to_parquet.py

# Check output:
# ⚠️  Skipping latest file (likely active): level2_20251114.txt
# 🔄 Processing: level2_20251107.txt ✓
# 🔄 Processing: level2_20251108.txt ✓

# Verify Parquet files created
ls datasets/parquet/level2/

# Output:
# date=2025-11-07/
# date=2025-11-08/
# (no date=2025-11-14 ← correctly skipped!)
```

---

This ensures your pipeline is **safe, automated, and production-ready**! 🎉

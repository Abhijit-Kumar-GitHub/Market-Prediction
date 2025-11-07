# Disk Space Monitoring Guide

## Quick Commands for Jupyter Lab Terminal

### 1. Check Total Disk Space Available
```bash
df -h .
```
This shows total disk space, used, and available for the current directory.

### 2. Check Your Project Folder Size
```bash
du -sh ~/MarketPrediction
```
Shows total size of your project folder.

### 3. Check Data Folder Size (More Detailed)
```bash
du -h crypto_data_jsonl/
```
Shows size of each file in the data folder.

### 4. Monitor Data Collection in Real-Time
```bash
watch -n 60 'du -sh crypto_data_jsonl/'
```
Updates every 60 seconds showing folder size growth.

## Expected Disk Usage

### Estimation for 2 Weeks:
- **BTC-USD Level 2 data**: ~50-100 MB per hour = 1.2-2.4 GB per day
- **ETH-USD Level 2 data**: ~30-70 MB per hour = 0.7-1.7 GB per day
- **Ticker data**: ~5-10 MB per day (much smaller)
- **Total per day**: ~2-5 GB
- **14 days total**: **30-70 GB**

### Rule of Thumb:
If the server has **100+ GB free**, you're safe for 2 weeks.
If less than 50 GB free, you might need to:
- Collect only 7 days instead of 14
- Collect only 1 coin (BTC-USD) instead of 2
- Ask lab admin for more space

## Daily Monitoring Checklist

Run these commands once per day:

```bash
# 1. Check remaining disk space
df -h .

# 2. Check your data size
du -sh crypto_data_jsonl/

# 3. Count number of files
ls -l crypto_data_jsonl/ | wc -l

# 4. Check latest file to confirm still collecting
ls -lth crypto_data_jsonl/ | head -5
```

## Critical: Set Up Persistent Session

Your data collector might stop when you close the browser. Use `nohup`:

### If NOT already running with nohup:
1. Stop current process: Press `Ctrl+C` in terminal
2. Restart with nohup:
```bash
nohup python run_collector_24x7.py > collector.log 2>&1 &
```
3. Check it's running:
```bash
ps aux | grep run_collector
```
4. View logs:
```bash
tail -f collector.log
```

### Benefits of nohup:
- Keeps running even if you close browser/logout
- Output saved to `collector.log` file
- Can check logs anytime remotely

## Remote Access Best Practices

### When You Leave the Lab:
1. **Don't close the terminal** - just close the browser tab
2. Or better: use `nohup` method above
3. Access remotely: Open browser → `http://IP:PORT` → Enter password
4. Open new terminal to check status

### Daily Remote Check (5 minutes):
1. Login to Jupyter Lab from anywhere
2. Open terminal
3. Run: `du -sh crypto_data_jsonl/` (check size growing)
4. Run: `tail collector.log` (check for errors)
5. Logout - collection continues

## What to Watch For

### Good Signs:
- Folder size increases by 2-5 GB per day
- New files created daily (level2_YYYYMMDD.txt, ticker_YYYYMMDD.txt)
- Log shows WebSocket connections active
- No error messages in log

### Warning Signs:
- Folder size stopped growing
- No new files for 24 hours
- Disk space below 10 GB
- Log shows repeated connection errors

### If Collection Stops:
```bash
# Check if process running
ps aux | grep run_collector

# If not running, restart
nohup python run_collector_24x7.py > collector.log 2>&1 &

# Monitor restart
tail -f collector.log
```

## Space-Saving Options (If Needed)

If running low on disk space:

### Option 1: Compress Old Data
```bash
gzip crypto_data_jsonl/level2_20251027.txt
gzip crypto_data_jsonl/ticker_20251027.txt
# Saves ~70% space
```

### Option 2: Collect Only BTC
Edit `data_collector.py` to remove ETH-USD from products list.

### Option 3: Shorter Collection Period
7-10 days still provides good data for analysis.

## Summary

**Disk Check**: Run `df -h .` → Need 100+ GB free for safety
**Remote Access**: Yes! Use browser from anywhere with IP:PORT:PASSWORD
**Persistence**: Use `nohup` command to keep running when browser closed
**Daily Check**: 5-minute remote login to verify size growing and no errors

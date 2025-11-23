# CSV Export & Power BI Quick Reference

## Quick Commands

### Export Parquet + CSV
```bash
# On DGX-A100
cd ~/Desktop/abhijit/MarketPrediction
python gpu/stage0_jsonl_to_parquet_v2.py --write-csv
```

### Export Parquet Only (Default)
```bash
python gpu/stage0_jsonl_to_parquet_v2.py
```

### Check Output
```bash
# Check Parquet files
ls -lh datasets/parquet/level2/date=2025-11-07/product_id=BTC-USD/

# Check CSV files (if --write-csv used)
ls -lh datasets/parquet/level2/date=2025-11-07/product_id=BTC-USD/*.csv
```

---

## Power BI Desktop Import (3 Steps)

### Step 1: Transfer Files to Windows
```bash
# From DGX-A100, copy to Windows machine
scp -r nvlabs@dgx-server:~/Desktop/abhijit/MarketPrediction/datasets/parquet/ C:\data\
```

### Step 2: Open Power BI Desktop
```
Get Data → Folder
→ Browse to: C:\data\parquet\level2\
→ Combine & Transform Data
→ Close & Apply
```

### Step 3: Build Visuals
- Line chart: `timestamp` (X-axis) vs `price_level` (Y-axis)
- Slicer: `product_id`, `date`
- Card: Total rows, date range

---

## File Size Reference

| Format | Size (26M rows) | Import Speed |
|--------|-----------------|--------------|
| **Parquet** | 187 MB | 3-5 seconds |
| **CSV** | 450 MB | 15-30 seconds |

**Recommendation:** Use Parquet for best performance.

---

## Power BI Desktop Limits

| Scenario | Will It Fit? | Recommendation |
|----------|--------------|----------------|
| **Full dataset (200M rows)** | ✅ Local only | Use filtered import or aggregate |
| **30 days (25M rows)** | ✅ Local + Cloud | Good for dashboards |
| **7 days (6M rows)** | ✅ Local + Cloud | Best for sharing |

**Local:** Power BI Desktop on your PC (free, no limits)
**Cloud:** Power BI Service (free tier: 1 GB limit)

---

## Filtering Examples

### Import Last 30 Days Only
In Power Query Editor:
```m
Table.SelectRows(Source, each [timestamp] >= DateTime.AddDays(DateTime.LocalNow(), -30))
```

### Import BTC-USD Only
```m
Table.SelectRows(Source, each [product_id] = "BTC-USD")
```

### Aggregate to Hourly Data
```m
Table.Group(Source, {"Hour"}, {
    {"AvgPrice", each List.Average([price_level]), type number},
    {"Volume", each List.Sum([new_quantity]), type number}
})
```

---

## Troubleshooting

### "Cannot find CSV files"
→ Did you use `--write-csv` flag?
→ Check: `ls datasets/parquet/level2/date=*/product_id=*/*.csv`

### "File too large for Power BI Service"
→ Use Power BI Desktop locally (no limit)
→ Or filter to last 30 days (< 1 GB)

### "Dates imported as text"
→ In Power Query: Change Type → Date/Time
→ Or use Parquet (types preserved automatically)

---

## Full Documentation

- **Power BI Guide:** `docs/POWER_BI_IMPORT_GUIDE.md` (complete reference)
- **GPU Pipeline:** `gpu/README.md` (all pipeline stages)
- **Script Help:** `python gpu/stage0_jsonl_to_parquet_v2.py --help`

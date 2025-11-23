# Power BI Import Guide

This guide explains how to import the converted Parquet/CSV data into Power BI Desktop for visualization and analysis.

## Table of Contents
- [Quick Start](#quick-start)
- [Data Size Considerations](#data-size-considerations)
- [Import Methods](#import-methods)
- [Filtering Strategies](#filtering-strategies)
- [Best Practices](#best-practices)

---

## Quick Start

### Step 1: Export Data with CSV (Optional)

If you prefer CSV for Power BI compatibility:

```bash
# On DGX-A100 server
python gpu/stage0_jsonl_to_parquet_v2.py --write-csv
```

This creates both Parquet and CSV files in `datasets/parquet/` with partitioning:
```
datasets/parquet/level2/
  date=2025-11-07/
    product_id=BTC-USD/
      data.parquet  (187 MB)
      data.csv      (450 MB, if --write-csv used)
    product_id=ETH-USD/
      data.parquet  (158 MB)
      data.csv      (380 MB, if --write-csv used)
  date=2025-11-08/
    ...
```

### Step 2: Import into Power BI Desktop

**Option A: Import Parquet (Recommended)**
1. Open Power BI Desktop
2. Click **Get Data** → **More...**
3. Search for "**Folder**" connector
4. Browse to `datasets/parquet/level2/`
5. Click **Combine & Transform Data**
6. Power Query will automatically combine all partition files
7. Click **Close & Apply**

**Option B: Import CSV**
1. Open Power BI Desktop
2. Click **Get Data** → **Folder**
3. Browse to `datasets/parquet/level2/`
4. In the filter bar, type `*.csv` to show only CSV files
5. Click **Combine & Transform Data**
6. Power Query will combine all CSV files
7. Click **Close & Apply**

---

## Data Size Considerations

### Power BI Desktop Limits

| Edition | Dataset Size Limit | Cost |
|---------|-------------------|------|
| **Power BI Desktop (local)** | Limited by RAM (~10 GB practical) | Free |
| **Power BI Service (Free)** | 1 GB per dataset | Free |
| **Power BI Pro** | 10 GB per dataset | $10/user/month |
| **Power BI Premium** | 100+ GB per dataset | $4,995/month |

### Your Dataset Size

**Full Dataset (~200M rows):**
- Parquet on disk: ~2-3 GB compressed
- Power BI in-memory: ~1-2 GB (after compression)
- **Verdict:** ✅ Fits in Power BI Desktop (local), ❌ Too large for Power BI Service (free)

**Filtered Dataset (30 days):**
- ~25M rows
- Power BI in-memory: ~200-300 MB
- **Verdict:** ✅ Fits in Power BI Desktop and Service (free)

---

## Import Methods

### Method 1: Import Parquet (Best Performance)

**Advantages:**
- ✅ Faster import (columnar format)
- ✅ Smaller file size (compressed)
- ✅ Schema preserved (types correct)
- ✅ No encoding issues

**Steps:**
```
Power BI Desktop
→ Get Data → Folder
→ Select: datasets/parquet/level2/
→ Combine & Transform Data
→ Power Query will show all partitions
→ Close & Apply
```

**Power Query M Code (auto-generated):**
```m
let
    Source = Folder.Files("C:\Users\...\datasets\parquet\level2"),
    FilterParquet = Table.SelectRows(Source, each Text.EndsWith([Name], ".parquet")),
    CombineFiles = Table.Combine(
        List.Transform(FilterParquet[Content], each Parquet.Document(_))
    )
in
    CombineFiles
```

### Method 2: Import CSV (More Compatible)

**Advantages:**
- ✅ Universal compatibility
- ✅ Easy to inspect/debug
- ✅ Works with all Power BI versions

**Disadvantages:**
- ❌ Larger file size
- ❌ Slower import
- ❌ May need type corrections

**Steps:**
```
Power BI Desktop
→ Get Data → Folder
→ Select: datasets/parquet/level2/
→ Filter: *.csv
→ Combine & Transform Data
→ Check column types (dates, numbers)
→ Close & Apply
```

### Method 3: Load from Database (Best for Large Data)

For datasets > 2 GB, consider loading into a database first:

**PostgreSQL (Free):**
```bash
# Install PostgreSQL
# Create database
psql -U postgres -c "CREATE DATABASE crypto_data;"

# Load Parquet using pandas/dask
python scripts/load_to_postgres.py
```

**Power BI Connection:**
```
Get Data → PostgreSQL Database
→ Server: localhost
→ Database: crypto_data
→ DirectQuery mode (recommended for large data)
```

---

## Filtering Strategies

### Strategy 1: Filter by Date in Power Query

**Use Case:** Reduce dataset to recent data (e.g., last 30 days)

**Power Query M Code:**
```m
let
    Source = Folder.Files("C:\...\datasets\parquet\level2"),
    FilterParquet = Table.SelectRows(Source, each Text.EndsWith([Name], ".parquet")),
    CombineFiles = Table.Combine(
        List.Transform(FilterParquet[Content], each Parquet.Document(_))
    ),
    // Filter last 30 days
    FilterDate = Table.SelectRows(CombineFiles, each [timestamp] >= DateTime.AddDays(DateTime.LocalNow(), -30))
in
    FilterDate
```

### Strategy 2: Filter by Product

**Use Case:** Analyze only BTC-USD

**Power Query M Code:**
```m
let
    Source = Folder.Files("C:\...\datasets\parquet\level2\date=2025-11-07\product_id=BTC-USD"),
    // Only load BTC-USD partition
    ...
in
    ...
```

Or filter after loading:
```m
FilterProduct = Table.SelectRows(CombineFiles, each [product_id] = "BTC-USD")
```

### Strategy 3: Aggregate to Hourly Data

**Use Case:** Reduce tick data to hourly OHLC (Open, High, Low, Close)

**Power Query M Code:**
```m
let
    Source = ...,
    GroupByHour = Table.Group(
        Source,
        {"product_id", "Hour"},
        {
            {"Open", each List.First([price_level]), type number},
            {"High", each List.Max([price_level]), type number},
            {"Low", each List.Min([price_level]), type number},
            {"Close", each List.Last([price_level]), type number},
            {"Volume", each List.Sum([new_quantity]), type number}
        }
    )
in
    GroupByHour
```

---

## Best Practices

### 1. Use Partitioning

Power BI's Folder connector automatically handles partitioned data:
- Partition by `date` for time-series filtering
- Partition by `product_id` for symbol filtering
- Our script already creates: `date=YYYY-MM-DD/product_id=SYMBOL/`

### 2. Set Correct Data Types

After import, verify column types in Power Query:
```
timestamp       → DateTime
price_level     → Decimal Number (Fixed)
new_quantity    → Decimal Number (Fixed)
side            → Text
product_id      → Text
```

### 3. Create Relationships

If you have multiple tables:
```
Level2 Table
  ↓ (timestamp, product_id)
Ticker Table
  ↓ (timestamp, product_id)
Products Table (lookup)
```

### 4. Use Import vs DirectQuery

| Mode | When to Use | Pros | Cons |
|------|-------------|------|------|
| **Import** | Data fits in memory (<2 GB) | Fast queries, rich features | Refresh required, size limits |
| **DirectQuery** | Large data (>2 GB) | No size limits, always fresh | Slower queries, limited features |

### 5. Enable Incremental Refresh

**Power BI Pro/Premium Only:**

```
1. Create RangeStart and RangeEnd parameters
2. Filter data: [timestamp] >= RangeStart and [timestamp] < RangeEnd
3. Configure incremental refresh:
   - Archive data older than 6 months
   - Refresh last 7 days
```

### 6. Optimize Visuals

For tick-level data (millions of rows):
- Use **aggregated measures** (avg, sum) instead of showing all rows
- **Sample data** for scatter plots (use Power Query `Table.FirstN(Source, 10000)`)
- **Bin timestamps** into 1-minute or 5-minute intervals
- Use **Line chart** instead of scatter for time series

---

## Example Power BI Report Structure

### Page 1: Overview Dashboard
- **Card:** Total Rows, Date Range, Products
- **Line Chart:** BTC-USD price over time (hourly aggregation)
- **Slicer:** Date range, Product selection

### Page 2: Order Book Depth
- **Stacked Area Chart:** Bid/Ask depth by price level
- **Table:** Top 10 bid/ask levels
- **Gauge:** Spread (best_ask - best_bid)

### Page 3: Volume Analysis
- **Column Chart:** Volume by hour
- **Heatmap:** Volume by hour × day of week
- **Card:** 24h volume, avg trade size

---

## Troubleshooting

### Issue: "File too large" error in Power BI Service

**Solution:** Filter data to last 30 days or aggregate before import.

### Issue: Dates imported as text

**Solution:** In Power Query, change type:
```m
ChangedType = Table.TransformColumnTypes(Source, {{"timestamp", type datetime}})
```

### Issue: Slow import from CSV

**Solution:** Use Parquet instead (10x faster).

### Issue: Out of memory in Power BI Desktop

**Solution:**
1. Close other applications
2. Filter data to smaller date range
3. Aggregate to hourly/daily data
4. Use 64-bit Power BI Desktop (supports more RAM)

---

## Sample Power Query Script

Complete example for filtered import:

```m
let
    // 1. Load Parquet files from folder
    Source = Folder.Files("C:\Users\abhijit\PycharmProjects\MarketPrediction\datasets\parquet\level2"),
    FilterParquet = Table.SelectRows(Source, each Text.EndsWith([Name], ".parquet")),
    
    // 2. Combine all partitions
    CombineFiles = Table.Combine(
        List.Transform(FilterParquet[Content], each Parquet.Document(_))
    ),
    
    // 3. Filter last 30 days
    FilterDate = Table.SelectRows(CombineFiles, 
        each [timestamp] >= DateTime.AddDays(DateTime.LocalNow(), -30)
    ),
    
    // 4. Filter BTC-USD only
    FilterProduct = Table.SelectRows(FilterDate, each [product_id] = "BTC-USD"),
    
    // 5. Set correct data types
    ChangedType = Table.TransformColumnTypes(FilterProduct, {
        {"timestamp", type datetime},
        {"price_level", type number},
        {"new_quantity", type number},
        {"sequence_num", Int64.Type},
        {"side", type text},
        {"product_id", type text}
    }),
    
    // 6. Add custom columns
    AddedHour = Table.AddColumn(ChangedType, "Hour", 
        each DateTime.Date([timestamp]) & Time.StartOfHour(DateTime.Time([timestamp])),
        type datetime
    )
in
    AddedHour
```

---

## Next Steps

1. **Test import** with one day of data first
2. **Build a prototype dashboard** with key metrics
3. **Optimize** with aggregations and filters
4. **Share** as .pbix file or publish to Power BI Service (if dataset < 1 GB)

For questions or issues, see:
- [Power BI Documentation](https://docs.microsoft.com/en-us/power-bi/)
- [Power Query M Reference](https://docs.microsoft.com/en-us/powerquery-m/)
- Project README for data schema details

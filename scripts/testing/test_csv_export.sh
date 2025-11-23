#!/bin/bash
# Test CSV Export on DGX-A100
# This script tests the new --write-csv feature on a single file

echo "=========================================="
echo "CSV Export Test"
echo "=========================================="
echo ""

# 1. Check available JSONL files
echo "Step 1: Checking available JSONL files..."
ls -lh crypto_data_jsonl/level2_*.txt | head -5
echo ""

# 2. Run conversion with CSV export on ONE file only
echo "Step 2: Running conversion with --write-csv (test on one date)..."
echo "Command: python gpu/stage0_jsonl_to_parquet_v2.py --write-csv"
echo ""

# Backup existing output (if any)
if [ -d "datasets/parquet/level2/" ]; then
    echo "Backing up existing Parquet files..."
    mv datasets/parquet/level2/ datasets/parquet/level2_backup_$(date +%Y%m%d_%H%M%S)/
fi

# Run the conversion
python gpu/stage0_jsonl_to_parquet_v2.py --write-csv

# 3. Verify output
echo ""
echo "=========================================="
echo "Step 3: Verifying output..."
echo "=========================================="
echo ""

# Check Parquet files
echo "Parquet files:"
find datasets/parquet/level2/ -name "*.parquet" -exec ls -lh {} \; | head -10
echo ""

# Check CSV files
echo "CSV files:"
find datasets/parquet/level2/ -name "*.csv" -exec ls -lh {} \; | head -10
echo ""

# 4. Compare file sizes
echo "=========================================="
echo "Step 4: File size comparison"
echo "=========================================="
echo ""

for dir in datasets/parquet/level2/date=*/product_id=*/; do
    if [ -d "$dir" ]; then
        echo "Directory: $dir"
        parquet_size=$(stat -c%s "$dir/data.parquet" 2>/dev/null || echo "0")
        csv_size=$(stat -c%s "$dir/data.csv" 2>/dev/null || echo "0")
        
        if [ "$parquet_size" != "0" ] && [ "$csv_size" != "0" ]; then
            parquet_mb=$(echo "scale=2; $parquet_size / 1024 / 1024" | bc)
            csv_mb=$(echo "scale=2; $csv_size / 1024 / 1024" | bc)
            ratio=$(echo "scale=2; $csv_size / $parquet_size" | bc)
            
            echo "  Parquet: ${parquet_mb} MB"
            echo "  CSV:     ${csv_mb} MB"
            echo "  Ratio:   ${ratio}x larger"
        fi
        echo ""
    fi
done

# 5. Test Power BI import (instructions)
echo "=========================================="
echo "Step 5: Power BI Import Test"
echo "=========================================="
echo ""
echo "To test in Power BI Desktop (on Windows):"
echo "1. Copy files to Windows:"
echo "   scp -r nvlabs@dgx-a100:~/Desktop/abhijit/MarketPrediction/datasets/parquet/ C:\\data\\"
echo ""
echo "2. Open Power BI Desktop"
echo "   Get Data -> Folder -> C:\\data\\parquet\\level2\\"
echo "   Combine & Transform Data"
echo ""
echo "3. Verify columns and row counts"
echo ""
echo "=========================================="
echo "Test complete!"
echo "=========================================="

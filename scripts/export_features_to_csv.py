"""
Export engineered features from parquet to CSV for Power BI analysis.

This script:
1. Loads all feature parquet files
2. Combines them into a single DataFrame
3. Exports to CSV for Power BI import mode
4. Provides summary statistics

Usage:
    python scripts/export_features_to_csv.py
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.gpu_config import PARQUET_FEATURES_DIR


def export_features_to_csv():
    """Export all engineered features to CSV for Power BI."""
    
    print("EXPORTING FEATURES TO CSV FOR POWER BI")
    print("="*70)
    
    # Find all feature files
    features_path = Path(PARQUET_FEATURES_DIR)
    all_files = sorted(list(features_path.glob("date=*/product_id=*/features.parquet")))
    
    if len(all_files) == 0:
        raise FileNotFoundError(f"No feature files found in {features_path}")
    
    print(f"\nFound {len(all_files)} feature files")
    
    # Load and combine all files
    print("\nLoading parquet files...")
    df_list = []
    
    for file in all_files:
        # Extract date and product from path
        parts = str(file).replace('\\', '/').split('/')
        date = [p for p in parts if 'date=' in p][0].split('=')[1]
        product = [p for p in parts if 'product_id=' in p][0].split('=')[1]
        
        # Load parquet
        df = pd.read_parquet(file)
        
        # Add date and product if not present
        if 'date' not in df.columns:
            df['date'] = date
        if 'product_id' not in df.columns:
            df['product_id'] = product
        
        df_list.append(df)
        print(f"  Loaded: {date} - {product} ({len(df):,} rows)")
    
    # Combine all DataFrames
    print("\nCombining DataFrames...")
    df_combined = pd.concat(df_list, ignore_index=True)
    
    print(f"✓ Combined {len(df_combined):,} total rows")
    print(f"  Columns: {len(df_combined.columns)}")
    print(f"  Memory usage: {df_combined.memory_usage(deep=True).sum() / 1e6:.2f} MB")
    
    # Create output directory
    output_dir = project_root / "powerbi_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to CSV
    output_path = output_dir / "features_complete.csv"
    print(f"\nExporting to CSV: {output_path}")
    
    # Handle null values for Power BI compatibility
    # Fill NaN with 0 (better than dropping for analysis)
    print("  Filling null values with 0 (for Power BI compatibility)...")
    df_combined = df_combined.fillna(0)
    
    df_combined.to_csv(output_path, index=False)
    
    print(f"\n✅ Export complete!")
    print(f"  Output: {output_path}")
    print(f"  Rows: {len(df_combined):,}")
    print(f"  Columns: {len(df_combined.columns)}")
    
    # Summary statistics
    print(f"\n📊 Dataset Summary:")
    print(f"  Columns: {list(df_combined.columns[:10])}{'...' if len(df_combined.columns) > 10 else ''}")
    
    # Date range
    if 'date' in df_combined.columns:
        print(f"  Date Range: {df_combined['date'].min()} to {df_combined['date'].max()}")
        print(f"  Unique Dates: {df_combined['date'].nunique()}")
    
    # Timestamp range
    if 'timestamp' in df_combined.columns:
        print(f"  Timestamp Range: {df_combined['timestamp'].min()} to {df_combined['timestamp'].max()}")
    
    # Products
    if 'product_id' in df_combined.columns:
        print(f"  Products: {df_combined['product_id'].unique().tolist()}")
    
    # Target variables
    targets = ['direction_10s', 'direction_30s', 'direction_60s']
    for target in targets:
        if target in df_combined.columns:
            dist = df_combined[target].value_counts()
            print(f"  {target} distribution:")
            for val, count in dist.items():
                print(f"    {val}: {count:,} ({count/len(df_combined)*100:.1f}%)")
    
    print("\n📌 Power BI Import Instructions:")
    print("  1. Open Power BI Desktop")
    print("  2. Get Data → Text/CSV")
    print(f"  3. Select: {output_path}")
    print("  4. Load (for Import mode - fastest)")
    print("  5. Create your visualizations!")
    
    return output_path


if __name__ == "__main__":
    try:
        output_path = export_features_to_csv()
        print(f"\n✅ Success! CSV ready for Power BI at:")
        print(f"   {output_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

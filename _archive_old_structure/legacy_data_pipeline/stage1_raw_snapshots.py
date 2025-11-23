"""
Stage 1: Convert JSONL .txt files to raw CSV
Pure conversion - just flatten JSON events to CSV rows, no aggregation

Run from project root: python data_pipeline/stage1_raw_snapshots.py
"""
import json
import csv
from pathlib import Path
import os

# Ensure we're working from project root
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)


def convert_level2_to_csv(txt_file, csv_file):
    """Convert level2 JSONL to CSV - one row per order book update"""
    print(f"Converting {txt_file} → {csv_file}")
    
    fieldnames = ['timestamp', 'event_type', 'product_id', 'side', 'price_level', 'new_quantity']
    
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        line_count = 0
        row_count = 0
        
        with open(txt_file, 'r') as f:
            for line in f:
                line_count += 1
                if line_count % 50000 == 0:
                    print(f"  Lines: {line_count:,} | Rows written: {row_count:,}")
                
                data = json.loads(line)
                if 'events' not in data:
                    continue
                
                timestamp = data['timestamp']
                
                for event in data['events']:
                    event_type = event.get('type')
                    product_id = event.get('product_id')
                    
                    if 'updates' in event:
                        for update in event['updates']:
                            writer.writerow({
                                'timestamp': timestamp,
                                'event_type': event_type,
                                'product_id': product_id,
                                'side': update.get('side'),
                                'price_level': update.get('price_level'),
                                'new_quantity': update.get('new_quantity')
                            })
                            row_count += 1
    
    print(f"  ✅ Done! {line_count:,} lines → {row_count:,} rows\n")
    return row_count


def convert_ticker_to_csv(txt_file, csv_file):
    """Convert ticker JSONL to CSV - one row per ticker event"""
    print(f"Converting {txt_file} → {csv_file}")
    
    fieldnames = [
        'timestamp', 'product_id', 'price', 'volume_24_h', 
        'low_24_h', 'high_24_h', 'price_percent_chg_24_h'
    ]
    
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        line_count = 0
        row_count = 0
        
        with open(txt_file, 'r') as f:
            for line in f:
                line_count += 1
                if line_count % 50000 == 0:
                    print(f"  Lines: {line_count:,} | Rows written: {row_count:,}")
                
                data = json.loads(line)
                if 'events' not in data:
                    continue
                
                timestamp = data['timestamp']
                
                for event in data['events']:
                    if 'tickers' not in event:
                        continue
                    
                    for ticker in event['tickers']:
                        writer.writerow({
                            'timestamp': timestamp,
                            'product_id': ticker.get('product_id'),
                            'price': ticker.get('price'),
                            'volume_24_h': ticker.get('volume_24_h'),
                            'low_24_h': ticker.get('low_24_h'),
                            'high_24_h': ticker.get('high_24_h'),
                            'price_percent_chg_24_h': ticker.get('price_percent_chg_24_h')
                        })
                        row_count += 1
    
    print(f"  ✅ Done! {line_count:,} lines → {row_count:,} rows\n")
    return row_count


def convert_all_files(input_folder='crypto_data_jsonl', output_folder='datasets/raw_csv'):
    """Convert all .txt files in input folder to CSV"""
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Converting all .txt files from: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"{'='*60}\n")
    
    total_rows = 0
    
    # Convert level2 files
    for txt_file in sorted(input_path.glob('level2_*.txt')):
        csv_file = output_path / txt_file.name.replace('.txt', '.csv')
        rows = convert_level2_to_csv(txt_file, csv_file)
        total_rows += rows
    
    # Convert ticker files
    for txt_file in sorted(input_path.glob('ticker_*.txt')):
        csv_file = output_path / txt_file.name.replace('.txt', '.csv')
        rows = convert_ticker_to_csv(txt_file, csv_file)
        total_rows += rows
    
    print(f"{'='*60}")
    print(f"✅ All files converted! Total rows: {total_rows:,}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # Convert all files
    convert_all_files()
    
    # Or convert specific files:
    # convert_level2_to_csv('crypto_data_jsonl/level2_20251107.txt', 'datasets/raw_csv/level2_20251107.csv')
    # convert_ticker_to_csv('crypto_data_jsonl/ticker_20251107.txt', 'datasets/raw_csv/ticker_20251107.csv')

"""
Stage 2: OrderBook Builder - Event Log → Market Snapshots
Reads level2 event log + ticker data, maintains order book state, outputs wide snapshots

Run from project root: python data_pipeline/stage2_orderbook_builder.py
"""
import pandas as pd
import csv
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
import os

# Ensure we're working from project root
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)


class OrderBook:
    """Maintains order book state for a single product"""
    
    def __init__(self, product_id):
        self.product_id = product_id
        self.bids = {}  # price -> quantity
        self.asks = {}  # price -> quantity
        
    def apply_snapshot(self, events_df):
        """Apply snapshot events (clear book and rebuild)"""
        self.bids.clear()
        self.asks.clear()
        
        for _, row in events_df.iterrows():
            price = float(row['price_level'])
            qty = float(row['new_quantity'])
            
            if row['side'] == 'bid':
                self.bids[price] = qty
            else:  # 'offer' in the data
                self.asks[price] = qty
    
    def apply_update(self, side, price, quantity, filter_outliers=True, last_mid_price=None):
        """Apply a single update event"""
        price = float(price)
        quantity = float(quantity)
        
        # Filter obvious bad data: prices >10% away from recent mid
        if filter_outliers and last_mid_price is not None:
            price_diff_pct = abs(price - last_mid_price) / last_mid_price
            if price_diff_pct > 0.10:  # More than 10% away
                return  # Skip this update
        
        if side == 'bid':
            if quantity == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = quantity
        else:  # 'offer'
            if quantity == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = quantity
    
    def get_snapshot_features(self):
        """
        Compute snapshot features from current book state
        Returns: dict with best_bid, best_ask, bid_volume_10, ask_volume_10
        """
        if not self.bids or not self.asks:
            return None
        
        # Sort and get top 10 levels
        top_bids = sorted(self.bids.items(), reverse=True)[:10]
        top_asks = sorted(self.asks.items())[:10]
        
        best_bid = top_bids[0][0]
        best_ask = top_asks[0][0]
        
        # Skip crossed book (data quality issue)
        if best_bid >= best_ask:
            return None
        
        bid_volume_10 = sum(qty for _, qty in top_bids)
        ask_volume_10 = sum(qty for _, qty in top_asks)
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'bid_volume_10': bid_volume_10,
            'ask_volume_10': ask_volume_10,
        }


class OrderBookSnapshotBuilder:
    """Builds market snapshots from event log + ticker data"""
    
    def __init__(self, level2_csv, ticker_csv, output_csv, snapshot_interval_seconds=10):
        self.level2_csv = level2_csv
        self.ticker_csv = ticker_csv
        self.output_csv = output_csv
        self.snapshot_interval_seconds = snapshot_interval_seconds
        
    def load_ticker_data(self):
        """Load ticker data into a lookup dict: timestamp -> product_id -> ticker_info"""
        # If no ticker file provided or file missing, return empty lookup
        if not self.ticker_csv:
            print("No ticker CSV provided - continuing without ticker join")
            return defaultdict(dict)

        try:
            print(f"Loading ticker data from {self.ticker_csv}...")
            ticker_df = pd.read_csv(self.ticker_csv)
            ticker_df['timestamp'] = pd.to_datetime(ticker_df['timestamp'])
        except Exception as e:
            print(f"Failed to load ticker CSV {self.ticker_csv}: {e}")
            return defaultdict(dict)

        # Create lookup: timestamp -> {product_id: {price, volume, ...}}
        ticker_lookup = defaultdict(dict)
        for _, row in ticker_df.iterrows():
            ts = row['timestamp']
            product_id = row['product_id']
            ticker_lookup[ts][product_id] = {
                'ticker_price': row.get('price', ''),
                'ticker_volume_24h': row.get('volume_24_h', ''),
                'ticker_low_24h': row.get('low_24_h', ''),
                'ticker_high_24h': row.get('high_24_h', ''),
                'ticker_price_change_24h_pct': row.get('price_percent_chg_24_h', ''),
            }

        print(f"Loaded {len(ticker_df):,} ticker events for {ticker_df['product_id'].nunique()} products")
        return ticker_lookup
    
    def build_snapshots(self):
        """Main pipeline: read events, maintain books, output snapshots"""
        
        # Load ticker data
        ticker_lookup = self.load_ticker_data()
        
        # Load level2 event log
        print(f"\nLoading level2 event log from {self.level2_csv}...")
        level2_df = pd.read_csv(self.level2_csv)
        level2_df['timestamp'] = pd.to_datetime(level2_df['timestamp'])
        
        print(f"Loaded {len(level2_df):,} level2 events")
        
        # Maintain order books per product
        orderbooks = {}  # product_id -> OrderBook
        last_snapshot_time = defaultdict(lambda: None)
        # NOTE: We DO NOT skip snapshots after the first one - reconnections send new snapshots
        # that must clear stale orderbook state
        
        # Output CSV writer
        output_file = open(self.output_csv, 'w', newline='')
        fieldnames = [
            'timestamp', 'product_id',
            'best_bid', 'best_ask', 'bid_volume_10', 'ask_volume_10',
            'ticker_price', 'ticker_volume_24h', 'ticker_low_24h', 
            'ticker_high_24h', 'ticker_price_change_24h_pct'
        ]
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        
        print(f"\nBuilding snapshots (interval: {self.snapshot_interval_seconds}s)...")
        print(f"Writing to {self.output_csv}...")
        
        snapshot_count = 0
        current_timestamp = None
        current_event_type = None
        current_product = None
        snapshot_events = []
        
        # Track event type stats
        event_type_counts = defaultdict(int)
        last_event_type = None
        crossed_book_count = 0
        
        # Process events
        for idx, row in level2_df.iterrows():
            if idx % 50000 == 0 and idx > 0:
                print(f"Processed {idx:,} events | Created {snapshot_count:,} snapshots | Event types: {dict(event_type_counts)}")
            
            event_type_counts[row['event_type']] += 1
            if row['event_type'] != last_event_type:
                if last_event_type is not None:
                    print(f"  → Event type changed: {last_event_type} → {row['event_type']} at event {idx:,}")
                last_event_type = row['event_type']
            
            timestamp = row['timestamp']
            event_type = row['event_type']
            product_id = row['product_id']
            
            # Initialize orderbook for product if not exists
            if product_id not in orderbooks:
                orderbooks[product_id] = OrderBook(product_id)
            
            # Handle snapshot events (they come in batches)
            if event_type == 'snapshot':
                if current_timestamp != timestamp or current_product != product_id:
                    # Process previous snapshot batch if exists
                    if snapshot_events:
                        events_df = pd.DataFrame(snapshot_events)
                        orderbooks[current_product].apply_snapshot(events_df)
                        snapshot_events = []
                        
                        # Always create a snapshot after processing snapshot batch
                        # This handles both initial connection AND reconnections
                        features = orderbooks[current_product].get_snapshot_features()
                        if features is not None:
                            ticker_data = ticker_lookup.get(current_timestamp, {}).get(current_product, {})
                            writer.writerow({
                                'timestamp': current_timestamp.isoformat(),
                                'product_id': current_product,
                                **features,
                                **ticker_data
                            })
                            snapshot_count += 1
                            last_snapshot_time[current_product] = current_timestamp
                    
                    current_timestamp = timestamp
                    current_product = product_id
                
                # Accumulate snapshot events
                snapshot_events.append({
                    'side': row['side'],
                    'price_level': row['price_level'],
                    'new_quantity': row['new_quantity']
                })
                
            elif event_type == 'update':
                # Process any pending snapshot first
                if snapshot_events:
                    events_df = pd.DataFrame(snapshot_events)
                    orderbooks[current_product].apply_snapshot(events_df)
                    snapshot_events = []
                    current_timestamp = None
                    current_product = None
                
                # Apply update
                orderbooks[product_id].apply_update(
                    row['side'],
                    row['price_level'],
                    row['new_quantity']
                )
                
                # Check if it's time to create a snapshot
                last_time = last_snapshot_time[product_id]
                if last_time is None:
                    time_diff = float('inf')
                else:
                    time_diff = (timestamp - last_time).total_seconds()
                
                if time_diff >= self.snapshot_interval_seconds:
                    # Get book features
                    features = orderbooks[product_id].get_snapshot_features()
                    
                    if features is None:
                        crossed_book_count += 1
                    
                    if features is not None:
                        # Find nearest ticker data
                        ticker_data = ticker_lookup.get(timestamp, {}).get(product_id, {})
                        
                        # If no exact match, try to find closest ticker within ±5 seconds
                        if not ticker_data:
                            for delta_sec in range(1, 6):
                                # Try future
                                future_ts = timestamp + pd.Timedelta(seconds=delta_sec)
                                ticker_data = ticker_lookup.get(future_ts, {}).get(product_id, {})
                                if ticker_data:
                                    break
                                
                                # Try past
                                past_ts = timestamp - pd.Timedelta(seconds=delta_sec)
                                ticker_data = ticker_lookup.get(past_ts, {}).get(product_id, {})
                                if ticker_data:
                                    break
                        
                        # Write snapshot row
                        writer.writerow({
                            'timestamp': timestamp.isoformat(),
                            'product_id': product_id,
                            **features,
                            **ticker_data  # Will be empty dict if no ticker found (CSV will have empty cells)
                        })
                        
                        snapshot_count += 1
                        last_snapshot_time[product_id] = timestamp
        
        # Process any final pending snapshot batch
        if snapshot_events and current_product:
            events_df = pd.DataFrame(snapshot_events)
            orderbooks[current_product].apply_snapshot(events_df)
            
            # Always create snapshot for final batch (handles reconnections)
            features = orderbooks[current_product].get_snapshot_features()
            if features is not None:
                ticker_data = ticker_lookup.get(current_timestamp, {}).get(current_product, {})
                writer.writerow({
                    'timestamp': current_timestamp.isoformat(),
                    'product_id': current_product,
                    **features,
                    **ticker_data
                })
                snapshot_count += 1
        
        output_file.close()
        
        print(f"\n✅ Completed!")
        print(f"Total events processed: {len(level2_df):,}")
        print(f"Event type breakdown: {dict(event_type_counts)}")
        print(f"Crossed books skipped: {crossed_book_count:,}")
        print(f"Total snapshots created: {snapshot_count:,}")
        print(f"Output: {self.output_csv}")


if __name__ == '__main__':
    import argparse
    from pathlib import Path

    p = argparse.ArgumentParser(description='Build orderbook snapshots from level2 event logs')
    p.add_argument('--level2', type=str, default=None, help='Path to a level2 CSV (if omitted, --all can be used)')
    p.add_argument('--ticker', type=str, default=None, help='Path to a ticker CSV (optional - will be inferred)')
    p.add_argument('--output', type=str, default=None, help='Output CSV path (optional)')
    p.add_argument('--interval', type=int, default=10, help='Snapshot interval in seconds')
    p.add_argument('--all', action='store_true', help='Process all level2_*.csv files in datasets/raw_csv/')
    args = p.parse_args()

    if args.all:
        raw_dir = Path('datasets/raw_csv')
        level2_files = sorted(raw_dir.glob('level2_*.csv'))
        if not level2_files:
            print('No level2_*.csv files found in datasets/raw_csv/')
        for lvl in level2_files:
            date_tag = lvl.stem.replace('level2_', '')
            ticker_candidate = raw_dir / f'ticker_{date_tag}.csv'
            out_file = Path('datasets') / f'market_snapshots_{date_tag}.csv'
            print(f'\n--- Processing date {date_tag}:')
            if not ticker_candidate.exists():
                print(f'  Warning: ticker file not found for {date_tag} -> {ticker_candidate} (ticker fields will be empty)')
                ticker_candidate = None
            builder = OrderBookSnapshotBuilder(
                level2_csv=str(lvl),
                ticker_csv=str(ticker_candidate) if ticker_candidate else None,
                output_csv=str(out_file),
                snapshot_interval_seconds=args.interval
            )
            builder.build_snapshots()
    else:
        # Single-run mode; require level2 file
        if not args.level2:
            print('Please provide --level2 <path> or use --all to process all files')
        else:
            level2_path = args.level2
            ticker_path = args.ticker
            out_path = args.output or 'datasets/market_snapshots.csv'
            builder = OrderBookSnapshotBuilder(
                level2_csv=level2_path,
                ticker_csv=ticker_path,
                output_csv=out_path,
                snapshot_interval_seconds=args.interval
            )
            builder.build_snapshots()

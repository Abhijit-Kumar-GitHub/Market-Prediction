# feature_engineer.py
"""
Transform raw JSONL data into ML-ready features
"""
import json
import pandas as pd
from datetime import datetime
from collections import defaultdict


class FeatureEngineer:
    def __init__(self, level2_file, ticker_file):
        self.level2_file = level2_file
        self.ticker_file = ticker_file
        
    def parse_level2(self):
        """Parse level2 data into order book snapshots"""
        orderbook = defaultdict(lambda: {'bids': {}, 'asks': {}})
        snapshots = []
        
        with open(self.level2_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'events' not in data:
                    continue
                    
                timestamp = data['timestamp']
                for event in data['events']:
                    if event['type'] != 'update':
                        continue
                        
                    product_id = event['product_id']
                    for update in event['updates']:
                        price = float(update['price_level'])
                        qty = float(update['new_quantity'])
                        side = update['side']
                        
                        # Update order book
                        book = orderbook[product_id]
                        if qty == 0:
                            # Remove level
                            book['bids' if side == 'bid' else 'asks'].pop(price, None)
                        else:
                            book['bids' if side == 'bid' else 'asks'][price] = qty
                    
                    # Create snapshot
                    snapshot = self._create_snapshot(
                        timestamp, product_id, orderbook[product_id]
                    )
                    if snapshot:
                        snapshots.append(snapshot)
        
        return pd.DataFrame(snapshots)
    
    def _create_snapshot(self, timestamp, product_id, orderbook):
        """Create feature vector from order book state"""
        bids = sorted(orderbook['bids'].items(), reverse=True)[:10]
        asks = sorted(orderbook['asks'].items())[:10]
        
        if not bids or not asks:
            return None
        
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        
        # Calculate features
        features = {
            'timestamp': timestamp,
            'product_id': product_id,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': (best_bid + best_ask) / 2,
            'spread': best_ask - best_bid,
            'spread_pct': (best_ask - best_bid) / best_bid * 100,
        }
        
        # Volume features
        bid_volume = sum(qty for _, qty in bids)
        ask_volume = sum(qty for _, qty in asks)
        features['bid_volume_10'] = bid_volume
        features['ask_volume_10'] = ask_volume
        features['order_imbalance'] = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        
        # Depth features (volume within 0.1% of mid)
        mid = features['mid_price']
        threshold = mid * 0.001
        
        depth_bid = sum(qty for price, qty in bids if abs(price - mid) <= threshold)
        depth_ask = sum(qty for price, qty in asks if abs(price - mid) <= threshold)
        features['depth_bid_0.1pct'] = depth_bid
        features['depth_ask_0.1pct'] = depth_ask
        
        return features
    
    def parse_ticker(self):
        """Parse ticker data for target variables"""
        tickers = []
        
        with open(self.ticker_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'events' not in data:
                    continue
                    
                timestamp = data['timestamp']
                for event in data['events']:
                    if 'tickers' not in event:
                        continue
                        
                    for ticker in event['tickers']:
                        tickers.append({
                            'timestamp': timestamp,
                            'product_id': ticker['product_id'],
                            'price': float(ticker['price']),
                            'volume_24h': float(ticker['volume_24_h']),
                            'price_change_24h_pct': float(ticker['price_percent_chg_24_h']),
                            'high_24h': float(ticker['high_24_h']),
                            'low_24h': float(ticker['low_24_h']),
                        })
        
        return pd.DataFrame(tickers)
    
    def merge_and_create_targets(self, orderbook_df, ticker_df, target_horizon=60):
        """
        Merge features with ticker data and create target variables
        
        target_horizon: seconds into the future to predict
        """
        # Convert timestamps to datetime
        orderbook_df['timestamp'] = pd.to_datetime(orderbook_df['timestamp'])
        ticker_df['timestamp'] = pd.to_datetime(ticker_df['timestamp'])
        
        # Merge on nearest timestamp (asof merge)
        df = pd.merge_asof(
            orderbook_df.sort_values('timestamp'),
            ticker_df.sort_values('timestamp'),
            on='timestamp',
            by='product_id',
            direction='nearest'
        )
        
        # Create target: price change in next N seconds
        df = df.sort_values(['product_id', 'timestamp'])
        df['future_price'] = df.groupby('product_id')['price'].shift(-target_horizon)
        df['price_change_pct'] = (
            (df['future_price'] - df['price']) / df['price'] * 100
        )
        
        # Classification target: Up/Down/Flat
        df['direction'] = pd.cut(
            df['price_change_pct'],
            bins=[-float('inf'), -0.05, 0.05, float('inf')],
            labels=['down', 'flat', 'up']
        )
        
        # Remove rows without future data
        df = df.dropna(subset=['future_price'])
        
        return df
    
    def run(self, output_file='features.csv'):
        """Full pipeline"""
        print("Parsing Level 2 data...")
        orderbook_df = self.parse_level2()
        print(f"Created {len(orderbook_df)} order book snapshots")
        
        print("\nParsing Ticker data...")
        ticker_df = self.parse_ticker()
        print(f"Created {len(ticker_df)} ticker records")
        
        print("\nMerging and creating targets...")
        features_df = self.merge_and_create_targets(orderbook_df, ticker_df)
        print(f"Final dataset: {len(features_df)} rows")
        
        print(f"\nSaving to {output_file}...")
        features_df.to_csv(output_file, index=False)
        print("Done!")
        
        return features_df


if __name__ == "__main__":
    # Test with your existing data
    engineer = FeatureEngineer(
        level2_file="crypto_data_jsonl/level2_20251028.txt",
        ticker_file="crypto_data_jsonl/ticker_20251028.txt"
    )
    
    df = engineer.run(output_file="crypto_features.csv")
    
    # Show sample
    print("\n" + "="*60)
    print("SAMPLE FEATURES:")
    print("="*60)
    print(df.head())
    print("\n" + "="*60)
    print("FEATURE STATISTICS:")
    print("="*60)
    print(df.describe())

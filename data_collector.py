# data_collector.py
import websocket
import json
import threading
import time
from datetime import datetime
import os
from collections import deque


class CryptoDataCollector:
    def __init__(self, output_dir="crypto_data_jsonl"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Buffers will now store raw JSON strings
        self.ticker_buffer = deque(maxlen=1000)
        self.level2_buffer = deque(maxlen=1000)

        # Get filenames for today
        self.ticker_file = ""
        self.level2_file = ""
        self.update_filenames()  # Set initial filenames

        # Track statistics
        self.stats = {
            'ticker_count': 0,
            'level2_count': 0,
            'start_time': datetime.now()
        }

        # Start flush thread
        self.running = True
        threading.Thread(target=self.periodic_flush, daemon=True).start()

    def update_filenames(self):
        """Sets the output filenames based on the current date"""
        date_str = datetime.now().strftime('%Y%m%d')
        self.ticker_file = f"{self.output_dir}/ticker_{date_str}.txt"
        self.level2_file = f"{self.output_dir}/level2_{date_str}.txt"
        print(f"\n[NEW FILES CREATED]\nTicker: {self.ticker_file}\nLevel2: {self.level2_file}\n")

    def flush_buffers(self):
        """Write buffered JSON strings to disk"""

        # Check if the date has changed (for file rotation)
        current_date = datetime.now().strftime('%Y%m%d')
        if not self.ticker_file.endswith(f"{current_date}.txt"):
            print("--- New day detected, rotating log files... ---")
            self.update_filenames()

        # Flush ticker data
        try:
            if self.ticker_buffer:
                # 'a' (append) mode will create the file if it doesn't exist
                with open(self.ticker_file, 'a') as f:
                    while self.ticker_buffer:
                        f.write(self.ticker_buffer.popleft() + '\n')

            # Flush level2 data
            if self.level2_buffer:
                with open(self.level2_file, 'a') as f:
                    while self.level2_buffer:
                        f.write(self.level2_buffer.popleft() + '\n')
        except Exception as e:
            print(f"Error flushing buffers: {e}")

    def periodic_flush(self):
        """Flush buffers every 30 seconds"""
        while self.running:
            time.sleep(30)
            self.flush_buffers()
            self.print_stats()

    def print_stats(self):
        """Print collection statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        if elapsed < 1:
            return

        print(f"\n--- Stats (Running for {elapsed / 60:.1f} min) ---")
        print(
            f"Ticker records: {self.stats['ticker_count']} (Rate: {self.stats['ticker_count'] / elapsed:.2f} msgs/sec)")
        print(
            f"Level2 records: {self.stats['level2_count']} (Rate: {self.stats['level2_count'] / elapsed:.2f} msgs/sec)")
        print("----------------------------------------\n")

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            # We still need to parse it once to check the channel
            data = json.loads(message)

            if 'channel' not in data:
                # Ignore system messages like 'subscriptions'
                if 'type' in data and data['type'] == 'subscriptions':
                    print("---!!! SUBSCRIPTION CONFIRMATION !!!---")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"Ignoring non-data message: {data}")
                return

            channel = data['channel']

            # Instead of parsing, just append the raw message string
            if channel == 'ticker':
                self.ticker_buffer.append(message)
                self.stats['ticker_count'] += 1

                if self.stats['ticker_count'] % 100 == 0:
                    print("Ticker")

            elif channel == 'l2_data':
                self.level2_buffer.append(message)
                self.stats['level2_count'] += 1

                if self.stats['level2_count'] % 1000 == 0:
                    print("Level2")

        except Exception as e:
            print(f"Error in on_message: {e} | Data: {message}")

    def on_open(self, ws):
        """Subscribe to channels on connection"""
        print("Connection opened")

        def run(*args):
            ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": ["BTC-USD", "ETH-USD"],
                "channel": "ticker"
            }))
            print("Subscribed to ticker")
            time.sleep(1)
            ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": ["BTC-USD", "ETH-USD"],
                "channel": "level2"
            }))
            print("Subscribed to level2")

        threading.Thread(target=run).start()

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")
        self.running = False
        self.flush_buffers()  # Final flush on close
        self.print_stats()

    def start(self):
        """Start the WebSocket connection"""
        socket_url = "wss://advanced-trade-ws.coinbase.com"
        ws = websocket.WebSocketApp(
            socket_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        print("Starting Coinbase data collection (JSONL Mode)...")
        print(f"Output directory: {self.output_dir}")
        print("Press Ctrl+C to stop\n")
        try:
            ws.run_forever()
        except KeyboardInterrupt:
            print("\nStopping collection...")
            self.running = False
            self.flush_buffers()  # Final flush on exit
            print("Goodbye.")


if __name__ == "__main__":
    collector = CryptoDataCollector(output_dir="crypto_data_jsonl")
    collector.start()
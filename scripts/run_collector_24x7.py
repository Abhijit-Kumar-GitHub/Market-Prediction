# run_collector_24x7.py
"""
Robust runner for 24/7 data collection with auto-restart on failures
"""
import subprocess
import time
from datetime import datetime
import os


def run_with_restart():
    """Run data_collector.py with automatic restart on crash"""
    consecutive_failures = 0
    max_consecutive_failures = 8
    
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"Starting data collector at {datetime.now()}")
            print(f"{'='*60}\n")
            
            # Run the collector with unbuffered output
            # Set PYTHONUNBUFFERED to force unbuffered output
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            process = subprocess.Popen(
                ['python', '-u', '../src/data/collector.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # Completely unbuffered
                universal_newlines=True,
                env=env
            )
            
            # Stream output in real-time
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line, end='', flush=True)
                    import sys
                    sys.stdout.flush()
            
            # Wait for process to complete
            return_code = process.wait()
            
            # Always restart on ANY exit (normal or crash)
            # This handles WebSocket disconnections
            consecutive_failures += 1
            
            if return_code == 0:
                print(f"\n🔄 Collector stopped (WebSocket disconnect?)")
            else:
                print(f"\n❌ Collector crashed (code {return_code})")
            
            print(f"Consecutive restarts: {consecutive_failures}/{max_consecutive_failures}")
            
            if consecutive_failures >= max_consecutive_failures:
                print("\n⛔ Too many consecutive failures. Stopping.")
                break
            
            # Wait before restart
            wait_time = 5  # Fixed 5 second wait
            print(f"⏳ Restarting in {wait_time} seconds...")
            time.sleep(wait_time)
            
            # Reset failure counter on successful restart
            consecutive_failures = 0
                
        except KeyboardInterrupt:
            print("\n\n⛔ Stopping data collection...")
            process.terminate()
            break
        except Exception as e:
            consecutive_failures += 1
            print(f"\n❌ Unexpected error: {e}")
            print(f"Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
            
            if consecutive_failures >= max_consecutive_failures:
                print("\n⛔ Too many consecutive failures. Stopping.")
                break
            
            time.sleep(5)


if __name__ == "__main__":
    print("🚀 24/7 Crypto Data Collector")
    print(f"Started: {datetime.now()}")
    print("Press Ctrl+C to stop\n")
    
    run_with_restart()
    
    print(f"\nStopped: {datetime.now()}")

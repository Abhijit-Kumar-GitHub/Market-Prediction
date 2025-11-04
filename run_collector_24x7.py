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
            
            # Run the collector
            process = subprocess.Popen(
                ['python', 'data_collector.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            for line in process.stdout:
                print(line, end='')
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                print("\nCollector stopped normally")
                consecutive_failures = 0
                break
            else:
                consecutive_failures += 1
                print(f"\nCollector crashed (code {return_code})")
                print(f"Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
                
                if consecutive_failures >= max_consecutive_failures:
                    print("\nToo many consecutive failures. Stopping.")
                    break
                
                # Wait before restart
                wait_time = min(60 * consecutive_failures, 300)  # Max 5 min
                print(f"Restarting in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n\n Stopping data collection...")
            process.terminate()
            break
        except Exception as e:
            consecutive_failures += 1
            print(f"\nUnexpected error: {e}")
            print(f"Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
            
            if consecutive_failures >= max_consecutive_failures:
                print("\n Too many consecutive failures. Stopping.")
                break
            
            time.sleep(60)


if __name__ == "__main__":
    print("🚀 24/7 Crypto Data Collector")
    print(f"Started: {datetime.now()}")
    print("Press Ctrl+C to stop\n")
    
    run_with_restart()
    
    print(f"\nStopped: {datetime.now()}")

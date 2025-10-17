#!/usr/bin/env python3
"""
Real-time indexing progress monitor with visual progress bar.
"""
import asyncio
import json
import time
from datetime import datetime
import requests
import sys

def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")

def create_progress_bar(percentage, width=50):
    """Create a visual progress bar."""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def format_time(seconds):
    """Format seconds into human readable time."""
    if seconds is None:
        return "Unknown"
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def monitor_indexing(task_id, base_url="http://localhost:8000"):
    """Monitor indexing progress with real-time updates."""
    status_url = f"{base_url}/api/index/status/{task_id}"
    
    print(f"🔍 Monitoring indexing task: {task_id}")
    print("=" * 60)
    
    start_time = time.time()
    last_status = None
    
    try:
        while True:
            try:
                response = requests.get(status_url, timeout=5)
                response.raise_for_status()
                status = response.json()
                
                # Clear screen and show header
                clear_screen()
                print(f"🔍 Indexing Monitor - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 60)
                print(f"Task ID: {task_id}")
                print(f"Repository: {status.get('repository_url', 'Unknown')}")
                print(f"Status: {status.get('status', 'Unknown').upper()}")
                print()
                
                # Show progress information
                progress = status.get('progress', {})
                if progress:
                    files_processed = progress.get('files_processed', 0)
                    total_files = progress.get('total_files', 0)
                    percentage = progress.get('percentage', 0)
                    current_file = progress.get('current_file')
                    bytes_processed = progress.get('bytes_processed', 0)
                    elapsed_time = progress.get('elapsed_time')
                    estimated_remaining = progress.get('estimated_remaining')
                    
                    # Progress bar
                    print("📊 Progress:")
                    print(f"  {create_progress_bar(percentage)}")
                    print()
                    
                    # File processing info
                    if total_files > 0:
                        print(f"📁 Files: {files_processed}/{total_files}")
                        if current_file:
                            print(f"📄 Current: {current_file}")
                        print(f"💾 Bytes: {bytes_processed:,}")
                        print()
                    
                    # Time information
                    if elapsed_time is not None:
                        print(f"⏱️  Elapsed: {format_time(elapsed_time)}")
                        if estimated_remaining is not None:
                            print(f"⏳ Remaining: {format_time(estimated_remaining)}")
                        print()
                
                # Show message
                message = status.get('message', '')
                if message:
                    print(f"💬 {message}")
                    print()
                
                # Check if completed or failed
                status_type = status.get('status')
                if status_type == 'completed':
                    print("✅ INDEXING COMPLETED SUCCESSFULLY!")
                    result = status.get('result', {})
                    if result:
                        print(f"   Files processed: {result.get('files_processed', 0)}")
                        print(f"   Total bytes: {result.get('total_bytes', 0):,}")
                        print(f"   Processing time: {format_time(result.get('processing_time', 0))}")
                    break
                elif status_type == 'failed':
                    print("❌ INDEXING FAILED!")
                    error = status.get('error', 'Unknown error')
                    print(f"   Error: {error}")
                    break
                
                # Show last update time
                print(f"🔄 Last update: {datetime.now().strftime('%H:%M:%S')}")
                print("   Press Ctrl+C to stop monitoring")
                
                last_status = status
                time.sleep(1)  # Update every second
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching status: {e}")
                print("   Retrying in 5 seconds...")
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n\n👋 Monitoring stopped by user")
                break
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python monitor_indexing.py <task_id>")
        print("Example: python monitor_indexing.py 10b47901-4ea4-42d3-8fc7-33bfcc816517")
        sys.exit(1)
    
    task_id = sys.argv[1]
    monitor_indexing(task_id)

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Get the directory where this script is located
CURRENT_DIR = Path(__file__).resolve().parent

def main():
    """
    Run both featured.py and recent.py scripts to update the index.md file
    with featured Posts and recent Posts.
    """
    print("🔄 Updating featured and recent Posts...")
    print(f"---------------------------------------------------------------")

    
    # Run featured.py
    featured_script = CURRENT_DIR / "featured.py"
    print(f"📌 Running {featured_script.name}...")
    try:
        subprocess.run([sys.executable, str(featured_script)], check=True)
        print("✅ Featured post updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running featured.py: {e}")
    
    # Get number of recent Posts from command line (default to 5)
    num_recent = 5
    if len(sys.argv) > 1:
        try:
            num_recent = int(sys.argv[1])
        except ValueError:
            print(f"⚠️ Invalid number of recent Posts: {sys.argv[1]}. Using default of 5.")
    
    # Run recent.py with the specified limit
    recent_script = CURRENT_DIR / "recent.py"
    print(f"---------------------------------------------------------------")
    print(f"📋 Running {recent_script.name} (showing {num_recent} Posts)...")
    try:
        subprocess.run([sys.executable, str(recent_script), str(num_recent)], check=True)
        print("✅ Recent Posts updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running recent.py: {e}")
    
    print("🎉 Index.md has been updated!")
    print(f"---------------------------------------------------------------")
    print(" ")

    print("💌 Done!")

if __name__ == "__main__":
    main()
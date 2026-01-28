#!/usr/bin/env python3
"""Script for complete reinstallation of dependencies."""

import subprocess
import sys

def main():
    print("🔄 Removing old dependencies...")
    result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "instagrapi", "pydantic"])
    if result.returncode != 0:
        print("⚠️  Warning: Failed to uninstall some packages (may not be installed)")
    
    print("🧹 Clearing pip cache...")
    result = subprocess.run([sys.executable, "-m", "pip", "cache", "purge"])
    if result.returncode != 0:
        print("❌ Error: Failed to clear pip cache")
        sys.exit(1)
    
    print("📦 Installing new dependencies...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade", "--force-reinstall"])
    if result.returncode != 0:
        print("❌ Error: Failed to install dependencies")
        sys.exit(1)
    
    print("✅ Done!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Script for complete reinstallation of dependencies."""

import subprocess
import sys

def main():
    print("🔄 Removing old dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "instagrapi", "pydantic"])
    
    print("🧹 Clearing pip cache...")
    subprocess.run([sys.executable, "-m", "pip", "cache", "purge"])
    
    print("📦 Installing new dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade", "--force-reinstall"])
    
    print("✅ Done!")

if __name__ == "__main__":
    main()

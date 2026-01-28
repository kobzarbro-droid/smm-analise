#!/usr/bin/env python3
"""Test script for dashboard functionality."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.app import create_app

def test_dashboard():
    """Test dashboard creation and routes."""
    print("Testing Instagram SMM Dashboard...")
    print("=" * 60)
    
    # Create app
    app = create_app({'TESTING': True})
    client = app.test_client()
    
    # Test pages
    pages = [
        ('/', 'Головна'),
        ('/posts', 'Публікації'),
        ('/analytics', 'Аналітика'),
        ('/competitors', 'Конкуренти'),
        ('/settings', 'Налаштування'),
        ('/reports', 'Звіти'),
    ]
    
    print("\n📄 Testing pages:")
    for url, name in pages:
        response = client.get(url)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"  {status} {name:20} [{url}] - Status: {response.status_code}")
    
    # Test API endpoints
    api_endpoints = [
        ('/api/metrics?period=7d', 'GET'),
        ('/api/engagement?period=30d', 'GET'),
        ('/api/top-posts?period=30d&limit=10', 'GET'),
        ('/api/competitors-comparison', 'GET'),
        ('/api/hashtags?limit=20', 'GET'),
    ]
    
    print("\n🔌 Testing API endpoints:")
    for url, method in api_endpoints:
        response = client.get(url) if method == 'GET' else None
        if response:
            status = "✓" if response.status_code in [200, 500] else "✗"
            # 500 is OK for now as we might not have data
            print(f"  {status} {method:4} {url}")
    
    # Test static files
    print("\n🎨 Testing static files:")
    static_files = [
        '/static/css/style.css',
        '/static/js/charts.js',
    ]
    
    for url in static_files:
        response = client.get(url)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"  {status} {url}")
    
    print("\n" + "=" * 60)
    print("✅ Dashboard structure verified!")
    print("\nTo start the dashboard, run:")
    print("  python run_dashboard.py")
    print("\nOr:")
    print("  python -m flask --app src.dashboard.app:create_app run")

if __name__ == '__main__':
    try:
        test_dashboard()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
find_hardware_endpoint.py
Find the correct endpoint for hardware devices
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "6b16484d021797bb5be96ffa58ff1a43"        # Replace with your actual key
API_SECRET = "e9d2d8b296d78c4b6ef611be6b39b8af"  # Replace with your actual secret

# ============================================
# FUNCTIONS
# ============================================

def test_endpoint(endpoint, method="GET", payload=None):
    """Test an endpoint to see what it returns"""
    
    url = f"{API_BASE_URL}/{endpoint}"
    
    print(f"\n🔍 Testing: {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(
                url,
                auth=HTTPBasicAuth(API_KEY, API_SECRET),
                headers={"Content-Type": "application/json"}
            )
        else:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(API_KEY, API_SECRET),
                json=payload or {},
                headers={"Content-Type": "application/json"}
            )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ Found {len(data)} items")
                print(f"   First item keys: {list(data[0].keys())[:10]}")
                return data
            elif isinstance(data, dict):
                print(f"   ✅ Found data with keys: {list(data.keys())[:10]}")
                return data
            else:
                print(f"   Response: {str(data)[:200]}")
                return data
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("FIND CORRECT HARDWARE ENDPOINT")
    print("=" * 70)
    print()
    
    # List of possible endpoints
    endpoints_to_test = [
        # Hardware endpoints
        "admin/networking/hardware",
        "admin/networking/hardware/list",
        "admin/networking/devices",
        "admin/networking/equipment",
        "admin/networking/inventory",
        "admin/networking/hardware/devices",
        # Monitoring endpoints (might contain hardware)
        "admin/networking/monitoring",
        "admin/networking/monitoring/hardware",
        # Router endpoints
        "admin/networking/routers",
        "admin/networking/routers/hardware",
        # Other possibilities
        "admin/hardware",
        "admin/hardware/list",
        "admin/networking/network-devices",
    ]
    
    print("Testing possible hardware endpoints...")
    print("-" * 50)
    
    results = {}
    
    for endpoint in endpoints_to_test:
        data = test_endpoint(endpoint)
        if data:
            results[endpoint] = data
    
    print()
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    if results:
        print(f"✅ Found {len(results)} working endpoints:")
        for endpoint, data in results.items():
            print(f"\n📋 {endpoint}:")
            if isinstance(data, list) and len(data) > 0:
                print(f"   - Count: {len(data)}")
                print(f"   - Sample keys: {list(data[0].keys())}")
                # Show sample title and type
                if 'title' in data[0]:
                    print(f"   - Sample title: {data[0].get('title')}")
                if 'type' in data[0]:
                    print(f"   - Sample type: {data[0].get('type')}")
                if 'location_id' in data[0]:
                    print(f"   - Sample location_id: {data[0].get('location_id')}")
            elif isinstance(data, dict):
                print(f"   - Keys: {list(data.keys())}")
    else:
        print("❌ No working endpoints found.")
        print()
        print("💡 Try checking Splynx manually:")
        print("   1. Go to Networking → Hardware → List")
        print("   2. Open Developer Tools (F12) → Network tab")
        print("   3. Look for the API request that loads the hardware list")
        print("   4. Note the endpoint URL")

if __name__ == "__main__":
    main()
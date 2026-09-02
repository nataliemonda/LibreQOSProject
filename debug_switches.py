"""
debug_switches.py
Find the correct endpoint for creating switches
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "API Key"  # Replace with your actual key
API_SECRET = "Secret API"  # Replace with your actual secret

# ============================================
# TEST DIFFERENT ENDPOINTS
# ============================================

def test_endpoint(endpoint, method="GET", payload=None):
    """Test an endpoint to see if it exists"""
    
    url = f"{API_BASE_URL}/{endpoint}"
    
    print(f"\n🔍 Testing: {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(
                url,
                auth=HTTPBasicAuth(API_KEY, API_SECRET),
                headers={"Content-Type": "application/json"}
            )
        else:  # POST
            response = requests.post(
                url,
                auth=HTTPBasicAuth(API_KEY, API_SECRET),
                json=payload or {},
                headers={"Content-Type": "application/json"}
            )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Found! Response: {response.json()[:200] if response.json() else 'Empty'}")
            return True
        elif response.status_code == 404:
            print(f"   ❌ Not found (404)")
            return False
        else:
            print(f"   ❌ Status {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("SWITCH ENDPOINT FINDER")
    print("=" * 70)
    print()
    
    # List of possible switch endpoints to try
    endpoints_to_test = [
        # Different variations
        "admin/networking/switches",
        "admin/networking/switch",
        "admin/networking/device",
        "admin/networking/devices",
        "admin/networking/equipment",
        "admin/networking/switch/create",
        "admin/networking/switches/create",
        # Alternative paths
        "admin/networking/routers/switch",
        "admin/networking/routers/switches",
        # Maybe it's under monitoring
        "admin/networking/monitoring/switch",
        "admin/networking/monitoring/switches",
    ]
    
    print("Testing possible switch endpoints...")
    print("-" * 50)
    
    found_endpoints = []
    
    for endpoint in endpoints_to_test:
        if test_endpoint(endpoint):
            found_endpoints.append(endpoint)
    
    print()
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    if found_endpoints:
        print(f"✅ Found {len(found_endpoints)} working endpoints:")
        for ep in found_endpoints:
            print(f"   - {ep}")
    else:
        print("❌ No switch endpoints found.")
        print()
        print("Let's try to find what endpoints are available...")
        
        # Try to get the API root to see available endpoints
        print("\n🔍 Checking API root...")
        try:
            response = requests.get(
                f"{API_BASE_URL}/admin/networking",
                auth=HTTPBasicAuth(API_KEY, API_SECRET),
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {json.dumps(response.json(), indent=2)[:500]}")
        except Exception as e:
            print(f"   Error: {str(e)}")

if __name__ == "__main__":
    main()

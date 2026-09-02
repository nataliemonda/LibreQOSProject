"""
debug_router.py
Get an existing router to see the correct field structure
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "API Key"        # Replace with your actual key
API_SECRET = "Secret Key"  # Replace with your actual secret

# ============================================
# GET EXISTING ROUTER
# ============================================

def get_existing_routers():
    """Fetch existing routers to see their structure"""
    
    endpoint = f"{API_BASE_URL}/admin/networking/routers"
    
    print(f"📡 Fetching existing routers from: {endpoint}")
    print("-" * 50)
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's a list or dict
            if isinstance(data, list):
                print(f"✅ Found {len(data)} routers")
                if len(data) > 0:
                    print("\n📋 First router structure:")
                    print(json.dumps(data[0], indent=2))
                    
                    # Extract the nas_type from the first router
                    first_router = data[0]
                    nas_type = first_router.get('nas_type')
                    nas_ip = first_router.get('nas_ip')
                    print(f"\n🔑 Found nas_type: '{nas_type}'")
                    print(f"🔑 Found nas_ip: '{nas_ip}'")
                    
                    return data
            else:
                print(f"Response structure: {json.dumps(data, indent=2)}")
                return data
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def get_router_options():
    """Try to get the options for nas_type from the API"""
    
    # Try to find the API schema or options endpoint
    endpoints_to_try = [
        f"{API_BASE_URL}/admin/networking/routers/options",
        f"{API_BASE_URL}/admin/networking/routers/schema",
        f"{API_BASE_URL}/admin/networking/routers/fields",
        f"{API_BASE_URL}/admin/networking/routers/metadata",
    ]
    
    print("\n" + "=" * 70)
    print("🔍 Trying to find nas_type options...")
    print("=" * 70)
    
    for endpoint in endpoints_to_try:
        print(f"\n📡 Trying: {endpoint}")
        try:
            response = requests.get(
                endpoint,
                auth=HTTPBasicAuth(API_KEY, API_SECRET),
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {json.dumps(response.json(), indent=2)[:500]}...")
        except Exception as e:
            print(f"   Error: {str(e)}")

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("ROUTER DEBUGGER")
    print("=" * 70)
    print()
    
    # 1. Get existing routers
    routers = get_existing_routers()
    
    # 2. Try to find options
    get_router_options()

if __name__ == "__main__":
    main()

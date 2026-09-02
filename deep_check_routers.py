"""
deep_check_routers.py
Deep check what's happening with the created routers
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "API Key"        # Replace with your actual key
API_SECRET = "Secret API"  # Replace with your actual secret

# ============================================
# FUNCTIONS
# ============================================

def get_routers():
    """Fetch all routers from Splynx"""
    endpoint = f"{API_BASE_URL}/admin/networking/routers"
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def get_monitoring_devices():
    """Fetch all monitoring devices"""
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring"
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("DEEP CHECK: ROUTERS VS MONITORING")
    print("=" * 70)
    print()
    
    # 1. Get routers
    print("📡 Fetching routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers in ROUTERS table")
    print()
    
    # 2. Get monitoring devices
    print("📡 Fetching monitoring devices...")
    print("-" * 50)
    monitoring = get_monitoring_devices()
    print(f"✅ Found {len(monitoring)} devices in MONITORING table")
    print()
    
    # 3. Check routers with 10.11.1.x IP
    print("🔍 Checking 10.11.1.x routers...")
    print("-" * 50)
    
    router_ips = {}
    for router in routers:
        ip = router.get('ip', '')
        title = router.get('title', '')
        router_id = router.get('id', '')
        location_id = router.get('location_id', '')
        router_type = router.get('type', '')
        
        if ip.startswith('10.11.1.'):
            router_ips[ip] = {
                'title': title,
                'id': router_id,
                'location_id': location_id,
                'type': router_type,
                'source': 'routers'
            }
    
    print(f"📊 10.11.1.x routers in ROUTERS table: {len(router_ips)}")
    print()
    
    # 4. Check monitoring devices with 10.11.1.x IP
    monitoring_ips = {}
    for device in monitoring:
        ip = device.get('ip', '')
        title = device.get('title', '')
        device_id = device.get('id', '')
        device_type = device.get('type', '')
        location_id = device.get('location_id', '')
        
        if ip.startswith('10.11.1.'):
            monitoring_ips[ip] = {
                'title': title,
                'id': device_id,
                'location_id': location_id,
                'type': device_type,
                'source': 'monitoring'
            }
    
    print(f"📊 10.11.1.x devices in MONITORING table: {len(monitoring_ips)}")
    print()
    
    # 5. Compare
    print("=" * 70)
    print("📊 COMPARISON")
    print("=" * 70)
    
    print(f"Routers in ROUTERS table:     {len(router_ips)}")
    print(f"Routers in MONITORING table:  {len(monitoring_ips)}")
    print()
    
    # 6. Show sample of routers in ROUTERS table
    if router_ips:
        print("📋 Sample of 10.11.1.x routers in ROUTERS table:")
        print("-" * 50)
        for ip, data in list(router_ips.items())[:5]:
            print(f"   - {data['title']} (ID: {data['id']}, Location: {data['location_id']})")
        if len(router_ips) > 5:
            print(f"   ... and {len(router_ips) - 5} more")
    print()
    
    # 7. Show sample of routers in MONITORING table
    if monitoring_ips:
        print("📋 Sample of 10.11.1.x routers in MONITORING table:")
        print("-" * 50)
        for ip, data in list(monitoring_ips.items())[:5]:
            print(f"   - {data['title']} (ID: {data['id']}, Type: {data['type']})")
        if len(monitoring_ips) > 5:
            print(f"   ... and {len(monitoring_ips) - 5} more")
    print()
    
    # 8. Check if routers are in monitoring (should not be)
    if monitoring_ips:
        print("❌ PROBLEM: Routers found in MONITORING table!")
        print("   They should be in ROUTERS table only.")
        print()
        print("   This means they were created as monitoring devices (Type 5)")
        print("   instead of routers (Type 1).")
        
        # Check first one's type
        first = list(monitoring_ips.values())[0]
        print(f"   Example: {first['title']} is Type {first['type']}")
        if first['type'] == 5:
            print("   Type 5 = Access Point (not a router!)")
            print("   We need to ensure routers are created as Type 1.")
    else:
        print("✅ All 10.11.1.x devices are in ROUTERS table only.")
        print("   This is correct!")

if __name__ == "__main__":
    main()

"""
diagnose_routers.py
Check what routers actually exist in Splynx
"""

import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "6b16484d021797bb5be96ffa58ff1a43"        # Replace with your actual key
API_SECRET = "e28d331e6a85176dd44ef1d6f952697a"  # Replace with your actual secret

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
    print("ROUTER DIAGNOSTIC")
    print("=" * 70)
    print()
    
    # 1. Get all routers
    print("📡 Fetching routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers total")
    print()
    
    if not routers:
        print("❌ No routers found!")
        return
    
    # 2. Categorize routers by IP range
    router_10_11_1 = []
    router_10_11_2 = []
    router_10_11_3 = []
    router_other = []
    
    for router in routers:
        ip = router.get('ip', '')
        title = router.get('title', '')
        router_id = router.get('id', '')
        
        if ip.startswith('10.11.1.'):
            router_10_11_1.append({'title': title, 'ip': ip, 'id': router_id})
        elif ip.startswith('10.11.2.'):
            router_10_11_2.append({'title': title, 'ip': ip, 'id': router_id})
        elif ip.startswith('10.11.3.'):
            router_10_11_3.append({'title': title, 'ip': ip, 'id': router_id})
        else:
            router_other.append({'title': title, 'ip': ip, 'id': router_id})
    
    # 3. Show breakdown
    print("📊 Router Breakdown by IP Range:")
    print("-" * 50)
    print(f"   10.11.1.x:  {len(router_10_11_1)} routers")
    print(f"   10.11.2.x:  {len(router_10_11_2)} routers")
    print(f"   10.11.3.x:  {len(router_10_11_3)} routers")
    print(f"   Other IPs:  {len(router_other)} routers")
    print()
    
    # 4. Show sample of 10.11.1.x routers
    if router_10_11_1:
        print(f"📋 10.11.1.x Routers (showing first 10):")
        print("-" * 50)
        for r in router_10_11_1[:10]:
            print(f"   - {r['title']} ({r['ip']}) - ID: {r['id']}")
        if len(router_10_11_1) > 10:
            print(f"   ... and {len(router_10_11_1) - 10} more")
    else:
        print("❌ No routers found with IP 10.11.1.x")
    print()
    
    # 5. Show sample of 10.11.2.x routers
    if router_10_11_2:
        print(f"📋 10.11.2.x Routers (showing first 10):")
        print("-" * 50)
        for r in router_10_11_2[:10]:
            print(f"   - {r['title']} ({r['ip']}) - ID: {r['id']}")
        if len(router_10_11_2) > 10:
            print(f"   ... and {len(router_10_11_2) - 10} more")
    else:
        print("❌ No routers found with IP 10.11.2.x")
    print()
    
    # 6. Check monitoring devices for comparison
    print("📡 Fetching monitoring devices for comparison...")
    print("-" * 50)
    monitoring = get_monitoring_devices()
    print(f"✅ Found {len(monitoring)} monitoring devices")
    print()
    
    # 7. Count switches in monitoring
    switches = [m for m in monitoring if m.get('type') == 2]
    print(f"📊 Switches in monitoring: {len(switches)}")
    switches_10_11_2 = [s for s in switches if s.get('ip', '').startswith('10.11.2.')]
    print(f"   - 10.11.2.x switches: {len(switches_10_11_2)}")
    print()
    
    # 8. Check if routers are in monitoring (should not be)
    routers_in_monitoring = [m for m in monitoring if any(keyword in m.get('title', '').upper() for keyword in ['BRASS', 'BRAS', 'IPOE'])]
    print(f"📊 Router-like devices in monitoring: {len(routers_in_monitoring)}")
    print("   (These should NOT be here - they should be in Routers table)")
    if routers_in_monitoring:
        print("   First 5:")
        for r in routers_in_monitoring[:5]:
            print(f"   - {r.get('title')} (Type: {r.get('type')}, IP: {r.get('ip')})")
    print()
    
    # 9. Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total routers:        {len(routers)}")
    print(f"  10.11.1.x routers:  {len(router_10_11_1)}")
    print(f"  10.11.2.x routers:  {len(router_10_11_2)}")
    print(f"  10.11.3.x routers:  {len(router_10_11_3)}")
    print(f"Switches:             {len(switches)}")
    print(f"  10.11.2.x switches: {len(switches_10_11_2)}")
    print()
    
    if len(router_10_11_1) > 0:
        print("✅ The 10.11.1.x routers EXIST!")
        print("   They should appear in Splynx -> Networking -> Routers")
        print()
        print("🔍 If you can't see them, try:")
        print("   1. Refresh the page")
        print("   2. Check filters (make sure no filters are hiding them)")
        print("   3. Check the pagination (maybe they're on another page)")
        print("   4. Search for '10.11.1' in the search bar")
    else:
        print("❌ No 10.11.1.x routers found!")
        print("   We need to recreate them.")

if __name__ == "__main__":
    main()
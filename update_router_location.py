"""
update_router_location.py
Update routers with location_id using PUT method with full data
"""

import requests
from requests.auth import HTTPBasicAuth
import time
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "6b16484d021797bb5be96ffa58ff1a43"        # Replace with your actual key
API_SECRET = "55ffc74653e58f43978146e065c606e6"  # Replace with your actual secret

# Default location ID - CHANGE THIS to match your existing routers
DEFAULT_LOCATION_ID = 2  # Try 2 first (from existing routers)

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

def get_router_by_id(router_id):
    """Fetch a single router by ID"""
    endpoint = f"{API_BASE_URL}/admin/networking/routers/{router_id}"
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def put_router(router_id, router_data):
    """
    Update a router using PUT with full data
    """
    endpoint = f"{API_BASE_URL}/admin/networking/routers/{router_id}"
    
    try:
        response = requests.put(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=router_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201, 204]:
            return True, "Updated successfully"
        else:
            return False, f"PUT failed: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("UPDATE ROUTER LOCATION (PUT METHOD)")
    print("=" * 70)
    print()
    
    # 1. Get all routers
    print("📡 Fetching routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers")
    print()
    
    # 2. Find routers that need location (10.11.1.x)
    routers_to_update = []
    
    for router in routers:
        ip = router.get('ip', '')
        title = router.get('title', '')
        router_id = router.get('id', '')
        location_id = router.get('location_id', '')
        
        # Check if it's our created router (10.11.1.x) and missing location
        if ip.startswith('10.11.1.') and location_id == 0:
            routers_to_update.append({
                'id': router_id,
                'title': title,
                'ip': ip,
                'location_id': location_id
            })
    
    print(f"🔍 Found {len(routers_to_update)} routers that need location")
    print()
    
    if not routers_to_update:
        print("✅ No routers need updating!")
        return
    
    # Show sample
    print(f"📋 First 10 routers to update (location_id: {DEFAULT_LOCATION_ID}):")
    print("-" * 50)
    for r in routers_to_update[:10]:
        print(f"   - {r['title']} (ID: {r['id']}, Current Location: {r['location_id']})")
    if len(routers_to_update) > 10:
        print(f"   ... and {len(routers_to_update) - 10} more")
    print()
    
    # 3. Confirm
    confirm = input(f"⚠️  Update {len(routers_to_update)} routers with location_id={DEFAULT_LOCATION_ID}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Update cancelled.")
        return
    
    print()
    print("🚀 Updating routers...")
    print("-" * 50)
    
    # 4. Update each router
    success_count = 0
    failed_count = 0
    failed_routers = []
    
    for router in routers_to_update:
        print(f"   Updating: {router['title']} (ID: {router['id']})...", end=" ")
        
        # Get full router data first
        full_data = get_router_by_id(router['id'])
        
        if not full_data:
            print("❌ FAILED: Could not fetch router data")
            failed_count += 1
            failed_routers.append(router['title'])
            continue
        
        # Update location_id
        full_data['location_id'] = DEFAULT_LOCATION_ID
        
        # Send PUT request with full data
        success, message = put_router(router['id'], full_data)
        
        if success:
            success_count += 1
            print("✅ UPDATED")
        else:
            failed_count += 1
            failed_routers.append(router['title'])
            print(f"❌ FAILED: {message[:100]}...")
        
        time.sleep(0.3)
    
    # 5. Summary
    print()
    print("=" * 70)
    print("📊 UPDATE SUMMARY")
    print("=" * 70)
    print(f"✅ Updated:  {success_count}")
    print(f"❌ Failed:   {failed_count}")
    print(f"📋 Total:    {len(routers_to_update)}")
    print()
    
    if failed_routers:
        print("❌ Failed routers:")
        for title in failed_routers[:10]:
            print(f"   - {title}")
        if len(failed_routers) > 10:
            print(f"   ... and {len(failed_routers) - 10} more")
    print()
    
    if success_count > 0:
        print("🎉 Routers updated! They should now appear in Splynx.")
        print("   Refresh the page and check Networking -> Routers")
    else:
        print("⚠️ No routers were updated. Check the errors above.")

if __name__ == "__main__":
    main()
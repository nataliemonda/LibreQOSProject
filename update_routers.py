"""
update_routers.py
Update routers with location, address, and GPS so they appear in Splynx UI
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
API_SECRET = "4048561e9bf70a18c33191a333d27e51"  # Replace with your actual secret

# Default values for new routers
DEFAULT_LOCATION_ID = 2  # Change to your default location ID
DEFAULT_ADDRESS = "Default Location"
DEFAULT_GPS = "0.0,0.0"  # Change to your default GPS
DEFAULT_MONITORING_GROUP = 1

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

def update_router(router_data):
    """
    Update a router with location, address, and GPS
    """
    router_id = router_data.get('id')
    endpoint = f"{API_BASE_URL}/admin/networking/routers/{router_id}"
    
    # Get current data
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code != 200:
            return False, f"Failed to get router: {response.status_code}"
        
        current_data = response.json()
        
        # Update with required fields
        current_data['location_id'] = DEFAULT_LOCATION_ID
        current_data['address'] = DEFAULT_ADDRESS
        current_data['gps'] = DEFAULT_GPS
        current_data['monitoring_group'] = DEFAULT_MONITORING_GROUP
        
        # Send update
        response = requests.put(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=current_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201, 204]:
            return True, "Updated successfully"
        else:
            return False, f"Update failed: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("UPDATE ROUTERS WITH LOCATION & ADDRESS")
    print("=" * 70)
    print()
    
    # 1. Get all routers
    print("📡 Fetching routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers")
    print()
    
    # 2. Find routers that need updating (10.11.1.x range)
    routers_to_update = []
    
    for router in routers:
        ip = router.get('ip', '')
        title = router.get('title', '')
        router_id = router.get('id', '')
        location_id = router.get('location_id', '')
        address = router.get('address', '')
        
        # Check if it's our created router (10.11.1.x)
        if ip.startswith('10.11.1.'):
            # Check if it needs updating (missing location or address)
            if location_id == 0 or not address:
                routers_to_update.append({
                    'id': router_id,
                    'title': title,
                    'ip': ip,
                    'location_id': location_id,
                    'address': address or 'MISSING'
                })
    
    print(f"🔍 Found {len(routers_to_update)} routers that need updating")
    print()
    
    if not routers_to_update:
        print("✅ No routers need updating!")
        return
    
    # Show sample
    print("📋 First 10 routers to update:")
    print("-" * 50)
    for r in routers_to_update[:10]:
        print(f"   - {r['title']} (ID: {r['id']}, Location: {r['location_id']}, Address: {r['address']})")
    if len(routers_to_update) > 10:
        print(f"   ... and {len(routers_to_update) - 10} more")
    print()
    
    # 3. Confirm
    confirm = input(f"⚠️  Update {len(routers_to_update)} routers with location/address? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Update cancelled.")
        return
    
    print()
    print("🚀 Updating routers...")
    print("-" * 50)
    
    # 4. Update each router
    success_count = 0
    failed_count = 0
    
    for router in routers_to_update:
        print(f"   Updating: {router['title']} (ID: {router['id']})...", end=" ")
        
        success, message = update_router(router)
        
        if success:
            success_count += 1
            print("✅ UPDATED")
        else:
            failed_count += 1
            print(f"❌ FAILED: {message}")
        
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
    
    if success_count > 0:
        print("🎉 Routers updated! They should now appear in Splynx.")
        print("   Refresh the page and check Networking -> Routers")
    else:
        print("⚠️ No routers were updated. Check the errors above.")

if __name__ == "__main__":
    main()
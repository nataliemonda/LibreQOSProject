"""
patch_routers.py
Patch routers with location_id using PATCH method
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
API_SECRET = "ec5d547b49041728acf6392d436e0b25"  # Replace with your actual secret

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

def patch_router(router_id, location_id):
    """
    Patch a router with location_id using PATCH method
    """
    endpoint = f"{API_BASE_URL}/admin/networking/routers/{router_id}"
    
    # Only send the fields we want to update
    payload = {
        "location_id": location_id
    }
    
    try:
        response = requests.patch(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201, 204]:
            return True, "Patched successfully"
        else:
            return False, f"Patch failed: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("PATCH ROUTERS WITH LOCATION")
    print("=" * 70)
    print()
    
    # 1. Get all routers
    print("📡 Fetching routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers")
    print()
    
    # 2. Find routers that need location (10.11.1.x)
    routers_to_patch = []
    
    for router in routers:
        ip = router.get('ip', '')
        title = router.get('title', '')
        router_id = router.get('id', '')
        location_id = router.get('location_id', '')
        
        # Check if it's our created router (10.11.1.x) and missing location
        if ip.startswith('10.11.1.') and location_id == 0:
            routers_to_patch.append({
                'id': router_id,
                'title': title,
                'ip': ip,
                'location_id': location_id
            })
    
    print(f"🔍 Found {len(routers_to_patch)} routers that need location")
    print()
    
    if not routers_to_patch:
        print("✅ No routers need patching!")
        return
    
    # Show sample
    print(f"📋 First 10 routers to patch (location_id: {DEFAULT_LOCATION_ID}):")
    print("-" * 50)
    for r in routers_to_patch[:10]:
        print(f"   - {r['title']} (ID: {r['id']}, Current Location: {r['location_id']})")
    if len(routers_to_patch) > 10:
        print(f"   ... and {len(routers_to_patch) - 10} more")
    print()
    
    # 3. Confirm
    confirm = input(f"⚠️  Patch {len(routers_to_patch)} routers with location_id={DEFAULT_LOCATION_ID}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Update cancelled.")
        return
    
    print()
    print("🚀 Patching routers...")
    print("-" * 50)
    
    # 4. Patch each router
    success_count = 0
    failed_count = 0
    
    for router in routers_to_patch:
        print(f"   Patching: {router['title']} (ID: {router['id']})...", end=" ")
        
        success, message = patch_router(router['id'], DEFAULT_LOCATION_ID)
        
        if success:
            success_count += 1
            print("✅ PATCHED")
        else:
            failed_count += 1
            print(f"❌ FAILED: {message}")
        
        time.sleep(0.3)
    
    # 5. Summary
    print()
    print("=" * 70)
    print("📊 PATCH SUMMARY")
    print("=" * 70)
    print(f"✅ Patched:   {success_count}")
    print(f"❌ Failed:    {failed_count}")
    print(f"📋 Total:     {len(routers_to_patch)}")
    print()
    
    if success_count > 0:
        print("🎉 Routers patched! They should now appear in Splynx.")
        print("   Refresh the page and check Networking -> Routers")
        print()
        print(f"📝 If they still don't appear, try different location_id:")
        print("   - Check an existing router's location_id and use that value")
        print("   - Current default: {DEFAULT_LOCATION_ID}")
    else:
        print("⚠️ No routers were patched. Check the errors above.")

if __name__ == "__main__":
    main()
"""
fix_router_types.py
Updates router devices from Type 5 (Access Point) to Type 1 (Router)
"""

import requests
from requests.auth import HTTPBasicAuth
import time
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "API Key"        # Replace with your actual key
API_SECRET = "Secret Key"  # Replace with your actual secret

# ============================================
# FUNCTIONS
# ============================================

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
            print(f"❌ Failed to fetch: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def update_device_type(device_id, new_type):
    """Update a device's type"""
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring/{device_id}"
    
    try:
        # First get the current device data
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return False, f"Failed to get device: {response.status_code}"
        
        device_data = response.json()
        
        # Update the type
        device_data['type'] = new_type
        
        # Send the update
        response = requests.put(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=device_data,
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
    print("FIX ROUTER TYPES (Type 5 -> Type 1)")
    print("=" * 70)
    print()
    
    # 1. Get all devices
    print("📡 Fetching monitoring devices...")
    print("-" * 50)
    devices = get_monitoring_devices()
    print(f"✅ Found {len(devices)} devices")
    print()
    
    # 2. Find routers that are Type 5
    routers_to_fix = []
    
    for device in devices:
        title = device.get('title', '')
        device_type = device.get('type', '')
        device_id = device.get('id', '')
        ip = device.get('ip', '')
        
        # Check if it's a router (BRASS_IPOE, BRAS_IPOE, etc.)
        is_router = any(keyword in title.upper() for keyword in ['BRASS', 'BRAS', 'IPOE'])
        
        # Check if it's Type 5 (Access Point) instead of Type 1 (Router)
        if is_router and device_type == 5:
            routers_to_fix.append({
                'id': device_id,
                'title': title,
                'ip': ip,
                'current_type': device_type
            })
    
    print(f"🔍 Found {len(routers_to_fix)} routers incorrectly set as Type 5:")
    for router in routers_to_fix[:10]:
        print(f"   - {router['title']} (ID: {router['id']}, IP: {router['ip']})")
    if len(routers_to_fix) > 10:
        print(f"   ... and {len(routers_to_fix) - 10} more")
    print()
    
    if not routers_to_fix:
        print("✅ No routers need fixing!")
        return
    
    # 3. Confirm
    confirm = input(f"⚠️  Update {len(routers_to_fix)} routers from Type 5 to Type 1? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Update cancelled.")
        return
    
    print()
    print("🚀 Updating routers...")
    print("-" * 50)
    
    # 4. Update each router
    success_count = 0
    failed_count = 0
    
    for router in routers_to_fix:
        print(f"   Updating: {router['title']} (ID: {router['id']})...", end=" ")
        
        success, message = update_device_type(router['id'], 1)
        
        if success:
            success_count += 1
            print("✅ SUCCESS")
        else:
            failed_count += 1
            print(f"❌ FAILED: {message}")
        
        time.sleep(0.5)
    
    # 5. Summary
    print()
    print("=" * 70)
    print("📊 UPDATE SUMMARY")
    print("=" * 70)
    print(f"✅ Updated:  {success_count}")
    print(f"❌ Failed:   {failed_count}")
    print(f"📋 Total:    {len(routers_to_fix)}")
    print()
    
    if failed_count == 0:
        print("🎉 All routers fixed! They should now appear in the Routers section.")
    else:
        print("⚠️ Some routers failed to update. Check the errors above.")

if __name__ == "__main__":
    main()

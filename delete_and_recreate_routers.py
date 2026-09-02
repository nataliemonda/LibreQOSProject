"""
delete_and_recreate_routers.py
Deletes routers without location and recreates them with all proper fields
"""

import requests
from requests.auth import HTTPBasicAuth
import time
import json
import csv
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "API Key"        # Replace with your actual key
API_SECRET = "Secret Key"  # Replace with your actual secret

# Default values from your existing router (MAC_MANZ_BRASS_IPOE)
DEFAULT_LOCATION_ID = 2  # Location: Machakos
DEFAULT_MONITORING_GROUP = 1  # Main group
DEFAULT_PRODUCER = 1  # MikroTik
DEFAULT_SNMP_PORT = 161
DEFAULT_SNMP_COMMUNITY = "public"
DEFAULT_SNMP_VERSION = 2
DEFAULT_GPS = "-1.518953,37.238073"  # Machakos GPS
DEFAULT_ADDRESS = "Default Location"

# IP base for new routers (will use 10.11.1.x again since we're deleting the old ones)
IP_BASE = "10.11.1"

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

def delete_router(router_id):
    """Delete a router by ID"""
    endpoint = f"{API_BASE_URL}/admin/networking/routers/{router_id}"
    
    try:
        response = requests.delete(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [200, 201, 204]:
            return True, "Deleted successfully"
        else:
            return False, f"Delete failed: {response.status_code} - {response.text}"
    except Exception as e:
        return False, str(e)

def create_router(title, ip):
    """Create a router with all required fields"""
    endpoint = f"{API_BASE_URL}/admin/networking/routers"
    
    payload = {
        "title": title,
        "ip": ip,
        "type": "router",
        "producer": DEFAULT_PRODUCER,
        "active": 1,
        "nas_type": 10,
        "nas_ip": ip,
        "authorization_method": "dhcp_leases",
        "accounting_method": "none",
        "location_id": DEFAULT_LOCATION_ID,
        "monitoring_group": DEFAULT_MONITORING_GROUP,
        "gps": DEFAULT_GPS,
        "address": DEFAULT_ADDRESS,
        "model": "",
        "snmp_port": DEFAULT_SNMP_PORT,
        "snmp_community": DEFAULT_SNMP_COMMUNITY,
        "snmp_version": DEFAULT_SNMP_VERSION,
    }
    
    try:
        response = requests.post(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("DELETE & RECREATE ROUTERS (WITH PROPER FIELDS)")
    print("=" * 70)
    print()
    
    # 1. Get all routers
    print("📡 Fetching routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers")
    print()
    
    # 2. Find routers without location (10.11.1.x with location_id=0)
    routers_to_delete = []
    
    for router in routers:
        ip = router.get('ip', '')
        title = router.get('title', '')
        router_id = router.get('id', '')
        location_id = router.get('location_id', '')
        
        # Check if it's our created router (10.11.1.x) and missing location
        if ip.startswith('10.11.1.') and location_id == 0:
            routers_to_delete.append({
                'id': router_id,
                'title': title,
                'ip': ip,
                'location_id': location_id
            })
    
    print(f"🔍 Found {len(routers_to_delete)} routers to delete (no location)")
    print()
    
    if not routers_to_delete:
        print("✅ No routers need fixing!")
        return
    
    # Show sample
    print("📋 First 10 routers to delete:")
    print("-" * 50)
    for r in routers_to_delete[:10]:
        print(f"   - {r['title']} (ID: {r['id']}, IP: {r['ip']})")
    if len(routers_to_delete) > 10:
        print(f"   ... and {len(routers_to_delete) - 10} more")
    print()
    
    # 3. Confirm deletion
    confirm = input(f"⚠️  DELETE {len(routers_to_delete)} routers? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Deletion cancelled.")
        return
    
    print()
    print("🗑️ Deleting routers without location...")
    print("-" * 50)
    
    # 4. Delete routers
    deleted_count = 0
    failed_deletes = []
    
    for router in routers_to_delete:
        print(f"   Deleting: {router['title']} (ID: {router['id']})...", end=" ")
        
        success, message = delete_router(router['id'])
        
        if success:
            deleted_count += 1
            print("✅ DELETED")
        else:
            failed_deletes.append(router)
            print(f"❌ FAILED: {message}")
        
        time.sleep(0.3)
    
    print()
    print(f"✅ Deleted: {deleted_count}/{len(routers_to_delete)}")
    
    if failed_deletes:
        print(f"❌ Failed to delete: {len(failed_deletes)}")
        for r in failed_deletes[:5]:
            print(f"   - {r['title']}")
        if len(failed_deletes) > 5:
            print(f"   ... and {len(failed_deletes) - 5} more")
    print()
    
    if deleted_count == 0:
        print("❌ No routers were deleted. Cannot proceed.")
        return
    
    # 5. Recreate routers with proper fields
    print("🔄 Recreating routers with proper fields...")
    print("-" * 50)
    print(f"   Location ID: {DEFAULT_LOCATION_ID}")
    print(f"   Group: {DEFAULT_MONITORING_GROUP}")
    print(f"   GPS: {DEFAULT_GPS}")
    print()
    
    # Only recreate the ones we successfully deleted
    deleted_ids = [r['id'] for r in routers_to_delete if r not in failed_deletes]
    routers_to_create = [r for r in routers_to_delete if r not in failed_deletes]
    
    ip_counter = 1
    created_count = 0
    failed_creates = []
    
    for router in routers_to_create:
        title = router['title']
        ip = f"{IP_BASE}.{ip_counter}"
        ip_counter += 1
        
        print(f"   Creating: {title} ({ip})...", end=" ")
        
        success, response = create_router(title, ip)
        
        if success:
            created_count += 1
            print("✅ SUCCESS")
        else:
            failed_creates.append({'title': title, 'error': response})
            print(f"❌ FAILED: {response[:100]}...")
        
        time.sleep(0.5)
    
    print()
    print(f"✅ Created: {created_count}/{len(routers_to_create)}")
    
    if failed_creates:
        print(f"❌ Failed to create: {len(failed_creates)}")
        for item in failed_creates[:5]:
            print(f"   - {item['title']}: {item['error'][:100]}...")
        if len(failed_creates) > 5:
            print(f"   ... and {len(failed_creates) - 5} more")
    print()
    
    # 6. Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"🗑️ Deleted (no location): {deleted_count}")
    print(f"✅ Created (with proper fields): {created_count}")
    print(f"❌ Failed deletes: {len(failed_deletes)}")
    print(f"❌ Failed creates: {len(failed_creates)}")
    print()
    
    if created_count > 0:
        print("🎉 Routers recreated successfully with all proper fields!")
        print("   They should now appear in Splynx -> Networking -> Routers")
        print()
        print("📋 Fields added:")
        print(f"   - Location ID: {DEFAULT_LOCATION_ID}")
        print(f"   - Group: {DEFAULT_MONITORING_GROUP}")
        print(f"   - GPS: {DEFAULT_GPS}")
        print(f"   - SNMP: {DEFAULT_SNMP_COMMUNITY} (v{DEFAULT_SNMP_VERSION})")
    else:
        print("⚠️ No routers were recreated. Check the errors above.")

if __name__ == "__main__":
    main()

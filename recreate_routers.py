"""
recreate_routers.py
Deletes incorrectly created Type 5 routers and recreates them as Type 1
"""

import requests
from requests.auth import HTTPBasicAuth
import time
import json

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "AKPI Key"        # Replace with your actual key
API_SECRET = "Secret Key"  # Replace with your actual secret

# IP Base for new routers
IP_BASE = "10.11.3"

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

def delete_device(device_id):
    """Delete a monitoring device by ID"""
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring/{device_id}"
    
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
    """Create a router as Type 1 (proper router)"""
    endpoint = f"{API_BASE_URL}/admin/networking/routers"
    
    payload = {
        "title": title,
        "ip": ip,
        "type": "router",
        "producer": 1,
        "active": 1,
        "nas_type": 10,
        "nas_ip": ip,
        "authorization_method": "dhcp_leases",
        "accounting_method": "none",
        "model": "",
        "location_id": 0,
        "snmp_port": 161,
        "snmp_community": "public",
        "snmp_version": 2,
        "monitoring_group": 1,
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
    print("RECREATE ROUTERS (Delete Type 5, Create Type 1)")
    print("=" * 70)
    print()
    
    # 1. Get all devices
    print("📡 Fetching monitoring devices...")
    print("-" * 50)
    devices = get_monitoring_devices()
    print(f"✅ Found {len(devices)} devices")
    print()
    
    # 2. Find incorrect routers (Type 5 with BRASS/BRAS in title)
    routers_to_delete = []
    
    for device in devices:
        title = device.get('title', '')
        device_type = device.get('type', '')
        device_id = device.get('id', '')
        ip = device.get('ip', '')
        
        # Check if it's a router (BRASS_IPOE, BRAS_IPOE, etc.)
        is_router = any(keyword in title.upper() for keyword in ['BRASS', 'BRAS', 'IPOE'])
        
        # Check if it's Type 5 (Access Point) instead of Type 1 (Router)
        # and has IP in the 10.11.2.x range (our created ones)
        if is_router and device_type == 5 and ip.startswith('10.11.2.'):
            routers_to_delete.append({
                'id': device_id,
                'title': title,
                'ip': ip,
                'current_type': device_type
            })
    
    print(f"🔍 Found {len(routers_to_delete)} incorrect routers to delete:")
    if routers_to_delete:
        for router in routers_to_delete[:10]:
            print(f"   - {router['title']} (ID: {router['id']}, IP: {router['ip']})")
        if len(routers_to_delete) > 10:
            print(f"   ... and {len(routers_to_delete) - 10} more")
    print()
    
    if not routers_to_delete:
        print("✅ No incorrect routers found!")
        return
    
    # 3. Confirm deletion
    confirm = input(f"⚠️  Delete {len(routers_to_delete)} incorrect routers? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Deletion cancelled.")
        return
    
    print()
    print("🗑️ Deleting incorrect routers...")
    print("-" * 50)
    
    # 4. Delete incorrect routers
    deleted_count = 0
    failed_deletes = []
    
    for router in routers_to_delete:
        print(f"   Deleting: {router['title']} (ID: {router['id']})...", end=" ")
        
        success, message = delete_device(router['id'])
        
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
        for router in failed_deletes[:5]:
            print(f"   - {router['title']} (ID: {router['id']})")
        if len(failed_deletes) > 5:
            print(f"   ... and {len(failed_deletes) - 5} more")
    print()
    
    # 5. Recreate routers as Type 1
    print("🔄 Recreating routers as Type 1...")
    print("-" * 50)
    
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
            print(f"❌ FAILED: {response}")
        
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
    print(f"🗑️ Deleted (incorrect Type 5): {deleted_count}")
    print(f"✅ Created (correct Type 1):   {created_count}")
    print(f"❌ Failed deletes:             {len(failed_deletes)}")
    print(f"❌ Failed creates:             {len(failed_creates)}")
    print()
    
    if created_count > 0:
        print("🎉 Routers recreated successfully!")
        print(f"   {created_count} routers created as Type 1.")
        print("   They should now appear in the Routers section in Splynx.")
    else:
        print("⚠️ No routers were recreated. Check the errors above.")
    
    print()
    print("=" * 70)
    print("📋 Next Steps:")
    print("1. Check Splynx dashboard - routers should appear")
    print("2. Run check_devices.py to verify")
    print("3. Then we can proceed to create access devices")
    print("=" * 70)

if __name__ == "__main__":
    main()

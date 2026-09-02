"""
create_access_devices.py
Creates all missing access devices with proper location from parent router
"""

import requests
from requests.auth import HTTPBasicAuth
import csv
import time
import json
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "API Key"        # Replace with your actual key
API_SECRET = "Secret API"  # Replace with your actual secret

# Input files
MISSING_DEVICES_FILE = 'missing_monitoring.csv'
REGION_MAP_FILE = 'region_map.csv'

# Output files
RESULTS_FILE = 'access_device_creation_results.csv'
FAILED_FILE = 'access_device_creation_failed.csv'

# Default values
DEFAULT_PRODUCER = 1  # MikroTik
DEFAULT_SNMP_PORT = 161
DEFAULT_SNMP_COMMUNITY = "public"
DEFAULT_SNMP_VERSION = 2
DEFAULT_MONITORING_GROUP = 1
DEFAULT_DEVICE_TYPE = 5  # Access Point

# IP base for new access devices
IP_BASE = "10.11.5"

# ============================================
# LOAD DATA
# ============================================

def load_csv(filename):
    """Load CSV and return list of dicts"""
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        print(f"✅ Loaded {len(data)} rows from {filename}")
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return []

def save_csv(filename, data, fieldnames):
    """Save list of dicts to CSV"""
    if not data:
        print(f"⚠️ No data to save for {filename}")
        return
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"✅ Saved {len(data)} rows to {filename}")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")

# ============================================
# API FUNCTIONS
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
            print(f"❌ Failed to fetch routers: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching routers: {str(e)}")
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
            print(f"❌ Failed to fetch monitoring devices: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching monitoring devices: {str(e)}")
        return []

def create_monitoring_device(device_data):
    """Create a monitoring device (access point)"""
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring"
    
    try:
        response = requests.post(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=device_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# ============================================
# IP GENERATOR
# ============================================

class IPGenerator:
    def __init__(self, base_ip="10.11.5"):
        self.base = base_ip
        self.counter = 1
    
    def get_next_ip(self):
        ip = f"{self.base}.{self.counter}"
        self.counter += 1
        return ip

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("CREATE ACCESS DEVICES (WITH PROPER LOCATION)")
    print("=" * 70)
    print()
    
    # 1. Load missing devices
    print("📂 Loading missing devices...")
    print("-" * 50)
    missing_devices = load_csv(MISSING_DEVICES_FILE)
    print()
    
    if not missing_devices:
        print("❌ No missing devices found!")
        return
    
    # 2. Load region map
    region_map = load_csv(REGION_MAP_FILE)
    print()
    
    # 3. Get existing routers
    print("📡 Fetching existing routers...")
    print("-" * 50)
    routers = get_routers()
    print(f"✅ Found {len(routers)} routers")
    print()
    
    # 4. Build router lookup by region
    router_lookup = {}
    for router in routers:
        title = router.get('title', '')
        location_id = router.get('location_id', 0)
        router_id = router.get('id', '')
        
        # Extract region from router title (first part before underscore)
        if title:
            parts = title.split('_')
            if len(parts) >= 2:
                region = parts[0]  # e.g., MAC, MIG, KSM
                router_lookup[region] = {
                    'router_id': router_id,
                    'location_id': location_id,
                    'router_title': title
                }
    
    print(f"📋 Built lookup for {len(router_lookup)} regions")
    print()
    
    # 5. Get existing monitoring devices to skip duplicates
    print("📡 Fetching existing monitoring devices...")
    print("-" * 50)
    monitoring = get_monitoring_devices()
    existing_titles = set()
    for device in monitoring:
        title = device.get('title', '')
        if title:
            existing_titles.add(title.strip())
    print(f"✅ Found {len(existing_titles)} existing monitoring devices")
    print()
    
    # 6. Filter missing devices (skip already existing)
    devices_to_create = []
    skipped_count = 0
    unknown_region_count = 0
    
    for device in missing_devices:
        title = device.get('title', '').strip()
        region = device.get('region', '')
        
        if not title:
            continue
        
        if title in existing_titles:
            skipped_count += 1
            continue
        
        # Get region from device (first part of title)
        if not region:
            parts = title.split('_')
            region = parts[0] if parts else 'UNKNOWN'
        
        # Look up router for this region
        router_info = router_lookup.get(region)
        
        if not router_info:
            unknown_region_count += 1
            continue
        
        devices_to_create.append({
            'title': title,
            'region': region,
            'router_id': router_info['router_id'],
            'location_id': router_info['location_id'],
            'router_title': router_info['router_title']
        })
    
    print(f"📊 Summary:")
    print(f"   Total missing devices: {len(missing_devices)}")
    print(f"   Already exist (skipped): {skipped_count}")
    print(f"   Unknown region: {unknown_region_count}")
    print(f"   Ready to create: {len(devices_to_create)}")
    print()
    
    if unknown_region_count > 0:
        print(f"⚠️ {unknown_region_count} devices have unknown regions.")
        print("   These will need region mapping to be created.")
        print()
    
    if not devices_to_create:
        print("✅ No devices to create!")
        return
    
    # 7. Confirm
    confirm = input(f"⚠️  Create {len(devices_to_create)} access devices? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Creating access devices...")
    print("=" * 70)
    print()
    
    # 8. Create devices
    ip_generator = IPGenerator(IP_BASE)
    results = []
    failed = []
    created_count = 0
    
    print("📡 Creating Access Devices...")
    print("-" * 50)
    
    for device in devices_to_create:
        title = device['title']
        region = device['region']
        ip = ip_generator.get_next_ip()
        location_id = device['location_id']
        router_id = device['router_id']
        
        print(f"   Creating: {title} ({region}) -> {ip} (Location: {location_id})...", end=" ")
        
        # Build payload
        payload = {
            "title": title,
            "ip": ip,
            "type": DEFAULT_DEVICE_TYPE,  # 5 = Access Point
            "producer": DEFAULT_PRODUCER,
            "active": 1,
            "location_id": location_id,
            "monitoring_group": DEFAULT_MONITORING_GROUP,
            "model": "",
            "snmp_port": DEFAULT_SNMP_PORT,
            "snmp_community": DEFAULT_SNMP_COMMUNITY,
            "snmp_version": DEFAULT_SNMP_VERSION,
            "parent_id": router_id,  # Link to parent router
        }
        
        success, response = create_monitoring_device(payload)
        
        result = {
            'Region': region,
            'Device_Title': title,
            'IP': ip,
            'Location_ID': location_id,
            'Parent_Router_ID': router_id,
            'Status': 'SUCCESS' if success else 'FAILED',
            'Response': str(response) if success else response,
            'Timestamp': datetime.now().isoformat()
        }
        results.append(result)
        
        if success:
            created_count += 1
            print("✅ SUCCESS")
        else:
            failed.append(result)
            print(f"❌ FAILED: {response[:100]}...")
        
        time.sleep(0.3)
    
    print()
    print(f"✅ Access devices created: {created_count}/{len(devices_to_create)}")
    
    # 9. Save results
    print()
    print("💾 Saving results...")
    print("-" * 50)
    
    if results:
        save_csv(RESULTS_FILE, results, 
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Parent_Router_ID', 'Status', 'Response', 'Timestamp'])
    
    if failed:
        save_csv(FAILED_FILE, failed,
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Parent_Router_ID', 'Status', 'Response', 'Timestamp'])
    
    # 10. Summary
    print()
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"✅ Access devices created: {created_count}")
    print(f"❌ Failed:                {len(failed)}")
    print(f"⏭️ Skipped (already exist): {skipped_count}")
    print(f"❓ Unknown region:        {unknown_region_count}")
    print()
    
    if created_count > 0:
        print("🎉 Access devices created successfully!")
        print("   They should now appear in Splynx -> Networking -> Monitoring")
        print()
        print("📋 Fields added:")
        print(f"   - Type: {DEFAULT_DEVICE_TYPE} (Access Point)")
        print(f"   - Parent: Router (linked to parent router)")
        print(f"   - Location: Inherited from parent router")
    else:
        print("⚠️ No access devices were created. Check the errors above.")
    
    print()
    print("=" * 70)
    print("📋 Next Steps:")
    print("1. Check Splynx -> Networking -> Monitoring for new access devices")
    print("2. Run hierarchy_analyzer.py to verify")
    print("3. Done! 🎉")
    print("=" * 70)

if __name__ == "__main__":
    main()

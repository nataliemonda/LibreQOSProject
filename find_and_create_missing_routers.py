"""
find_and_create_missing_routers.py
Find and create missing routers in the monitoring endpoint
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
API_SECRET = "Secret Key"  # Replace with your actual secret

# Input files
REGION_MAP_FILE = 'region_map.csv'
ROUTER_CONTENTIONS_FILE = 'router_contentions.csv'

# Output files
RESULTS_FILE = 'missing_router_creation_results.csv'
FAILED_FILE = 'missing_router_creation_failed.csv'

# Default values
DEFAULT_PRODUCER = 1
DEFAULT_SNMP_PORT = 161
DEFAULT_SNMP_COMMUNITY = "public"
DEFAULT_SNMP_VERSION = 2
DEFAULT_TYPE = 1  # Router
DEFAULT_ACTIVE = 1
DEFAULT_SEND_NOTIFICATIONS = 0
DEFAULT_IS_PING = 1
DEFAULT_MONITORING_GROUP = 1

# IP base for new routers
IP_BASE = "10.11.8"

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
    """Create a device in the monitoring endpoint"""
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
    def __init__(self, base_ip="10.11.8"):
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
    print("FIND AND CREATE MISSING ROUTERS")
    print("=" * 70)
    print()
    
    # 1. Load region map
    print("📂 Loading region map...")
    print("-" * 50)
    region_map = load_csv(REGION_MAP_FILE)
    print()
    
    if not region_map:
        print("❌ No region map found!")
        return
    
    # 2. Get existing monitoring devices
    print("📡 Fetching existing monitoring devices...")
    print("-" * 50)
    monitoring = get_monitoring_devices()
    existing_titles = set()
    location_ids = {}
    
    for device in monitoring:
        title = device.get('title', '')
        if title:
            existing_titles.add(title.strip())
        
        loc_id = device.get('location_id')
        if loc_id:
            location_ids[loc_id] = location_ids.get(loc_id, 0) + 1
    
    print(f"✅ Found {len(monitoring)} monitoring devices")
    print()
    
    # 3. Determine location_id
    if location_ids:
        most_common_location = max(location_ids.items(), key=lambda x: x[1])[0]
        print(f"💡 Using most common location_id: {most_common_location}")
        LOCATION_ID = most_common_location
    else:
        LOCATION_ID = 41
        print(f"💡 Using default location_id: {LOCATION_ID}")
    print()
    
    # 4. Get all routers from region_map
    all_routers = []
    for row in region_map:
        region = row.get('region', '').strip()
        router_title = row.get('router_title', '').strip()
        county = row.get('county', '').strip()
        
        if not region or not router_title:
            continue
        
        all_routers.append({
            'region': region,
            'title': router_title,
            'county': county
        })
    
    print(f"📊 Total routers in region_map: {len(all_routers)}")
    print()
    
    # 5. Find missing routers (not in monitoring)
    missing_routers = []
    existing_count = 0
    
    for router in all_routers:
        title = router['title']
        if title in existing_titles:
            existing_count += 1
            print(f"   ✅ Already exists: {title}")
        else:
            missing_routers.append(router)
            print(f"   ❌ MISSING: {title}")
    
    print()
    print(f"📊 Summary:")
    print(f"   Total routers in region_map: {len(all_routers)}")
    print(f"   Already exist: {existing_count}")
    print(f"   Missing: {len(missing_routers)}")
    print()
    
    if not missing_routers:
        print("✅ All routers already exist!")
        return
    
    # 6. Confirm
    confirm = input(f"⚠️  Create {len(missing_routers)} missing routers? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Creating missing routers...")
    print("=" * 70)
    print()
    
    # 7. Create missing routers
    ip_generator = IPGenerator(IP_BASE)
    results = []
    failed = []
    created_count = 0
    
    print("📡 Creating Routers...")
    print("-" * 50)
    
    for router in missing_routers:
        title = router['title']
        region = router['region']
        ip = ip_generator.get_next_ip()
        
        print(f"   Creating: {title} ({region}) -> {ip}...", end=" ")
        
        payload = {
            "title": title,
            "ip": ip,
            "type": DEFAULT_TYPE,
            "producer": DEFAULT_PRODUCER,
            "active": DEFAULT_ACTIVE,
            "location_id": LOCATION_ID,
            "monitoring_group": DEFAULT_MONITORING_GROUP,
            "model": "",
            "snmp_port": DEFAULT_SNMP_PORT,
            "snmp_community": DEFAULT_SNMP_COMMUNITY,
            "snmp_version": DEFAULT_SNMP_VERSION,
            "send_notifications": DEFAULT_SEND_NOTIFICATIONS,
            "is_ping": DEFAULT_IS_PING,
            "address": "",
            "gps": "",
        }
        
        success, response = create_monitoring_device(payload)
        
        result = {
            'Region': region,
            'Device_Title': title,
            'IP': ip,
            'Location_ID': LOCATION_ID,
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
        
        time.sleep(0.5)
    
    print()
    print(f"✅ Routers created: {created_count}/{len(missing_routers)}")
    
    # 8. Save results
    print()
    print("💾 Saving results...")
    print("-" * 50)
    
    if results:
        save_csv(RESULTS_FILE, results, 
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Status', 'Response', 'Timestamp'])
    
    if failed:
        save_csv(FAILED_FILE, failed,
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Status', 'Response', 'Timestamp'])
    
    # 9. Summary
    print()
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"✅ Routers created:  {created_count}")
    print(f"❌ Failed:           {len(failed)}")
    print(f"⏭️ Already existed:  {existing_count}")
    print()
    
    if created_count > 0:
        print(f"🎉 {created_count} missing routers created successfully!")
        print("   They should now appear in Splynx -> Networking -> Hardware -> List")
    else:
        print("⚠️ No routers were created. Check the errors above.")

if __name__ == "__main__":
    main()

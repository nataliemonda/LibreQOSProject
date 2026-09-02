"""
create_all_routers_in_monitoring.py
Creates ALL missing routers in the monitoring endpoint
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
API_KEY = "6b16484d021797bb5be96ffa58ff1a43"        # Replace with your actual key
API_SECRET = "c58a43c88acdf8da9338b22c317d9e58"  # Replace with your actual secret

# Input files
ROUTER_CONTENTIONS_FILE = 'router_contentions.csv'
REGION_MAP_FILE = 'region_map.csv'

# Output files
RESULTS_FILE = 'all_router_creation_results.csv'
FAILED_FILE = 'all_router_creation_failed.csv'

# Default values
DEFAULT_PRODUCER = 1  # MikroTik
DEFAULT_SNMP_PORT = 161
DEFAULT_SNMP_COMMUNITY = "public"
DEFAULT_SNMP_VERSION = 2
DEFAULT_TYPE = 1  # Router
DEFAULT_ACTIVE = 1
DEFAULT_SEND_NOTIFICATIONS = 0
DEFAULT_IS_PING = 1
DEFAULT_MONITORING_GROUP = 1

# IP base for new routers
IP_BASE = "10.11.7"

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
    def __init__(self, base_ip="10.11.7"):
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
    print("CREATE ALL ROUTERS IN MONITORING")
    print("=" * 70)
    print()
    
    # 1. Load router contentions (all routers that should exist)
    print("📂 Loading router contentions...")
    print("-" * 50)
    router_contentions = load_csv(ROUTER_CONTENTIONS_FILE)
    print()
    
    if not router_contentions:
        print("❌ No router contentions found!")
        return
    
    # 2. Load region map
    region_map = load_csv(REGION_MAP_FILE)
    print()
    
    # 3. Build region to router mapping
    region_router_map = {}
    for row in region_map:
        region = row.get('region', '').strip()
        router_title = row.get('router_title', '').strip()
        if region and router_title:
            region_router_map[region] = router_title
    
    # 4. Get unique routers from contentions
    router_titles = set()
    router_regions = {}
    
    for device in router_contentions:
        title = device.get('title', '').strip()
        router_id = device.get('router_id', '').strip()
        
        if not title:
            continue
        
        # Check if this is a router (contains BRASS, BRAS, IPoE, etc.)
        is_router = any(keyword in title.upper() for keyword in ['BRASS', 'BRAS', 'IPOE'])
        
        if is_router:
            # Extract region from title (first part before underscore)
            parts = title.split('_')
            region = parts[0] if parts else 'UNKNOWN'
            
            # Try to get correct router title from region_map
            correct_title = region_router_map.get(region)
            if correct_title:
                router_titles.add(correct_title)
                router_regions[correct_title] = region
            else:
                # Use the title as is
                router_titles.add(title)
                router_regions[title] = region
    
    print(f"📊 Found {len(router_titles)} unique routers from contentions")
    print()
    
    # 5. Get existing monitoring devices
    print("📡 Fetching existing monitoring devices...")
    print("-" * 50)
    monitoring = get_monitoring_devices()
    existing_titles = set()
    location_ids = {}
    
    for device in monitoring:
        title = device.get('title', '')
        if title:
            existing_titles.add(title.strip())
        
        # Collect location_id mappings
        loc_id = device.get('location_id')
        if loc_id:
            location_ids[loc_id] = location_ids.get(loc_id, 0) + 1
    
    print(f"✅ Found {len(monitoring)} monitoring devices")
    print()
    
    # 6. Determine location_id
    if location_ids:
        most_common_location = max(location_ids.items(), key=lambda x: x[1])[0]
        print(f"💡 Using most common location_id: {most_common_location}")
        LOCATION_ID = most_common_location
    else:
        LOCATION_ID = 41
        print(f"💡 Using default location_id: {LOCATION_ID}")
    print()
    
    # 7. Filter routers to create (skip existing)
    routers_to_create = []
    skipped_count = 0
    
    for title in sorted(router_titles):
        if title in existing_titles:
            skipped_count += 1
            print(f"⏭️ Skipping: {title} - already exists")
        else:
            region = router_regions.get(title, 'UNKNOWN')
            routers_to_create.append({
                'title': title,
                'region': region
            })
    
    print()
    print(f"📊 Summary:")
    print(f"   Total routers: {len(router_titles)}")
    print(f"   Already exist (skipped): {skipped_count}")
    print(f"   Need to create: {len(routers_to_create)}")
    print()
    
    if not routers_to_create:
        print("✅ All routers already exist!")
        return
    
    # 8. Confirm
    confirm = input(f"⚠️  Create {len(routers_to_create)} routers? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Creating routers...")
    print("=" * 70)
    print()
    
    # 9. Create routers
    ip_generator = IPGenerator(IP_BASE)
    results = []
    failed = []
    created_count = 0
    
    print("📡 Creating Routers...")
    print("-" * 50)
    
    for router in routers_to_create:
        title = router['title']
        region = router['region']
        ip = ip_generator.get_next_ip()
        
        print(f"   Creating: {title} ({region}) -> {ip}...", end=" ")
        
        # Build payload
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
    print(f"✅ Routers created: {created_count}/{len(routers_to_create)}")
    
    # 10. Save results
    print()
    print("💾 Saving results...")
    print("-" * 50)
    
    if results:
        save_csv(RESULTS_FILE, results, 
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Status', 'Response', 'Timestamp'])
    
    if failed:
        save_csv(FAILED_FILE, failed,
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Status', 'Response', 'Timestamp'])
    
    # 11. Summary
    print()
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"✅ Routers created:  {created_count}")
    print(f"❌ Failed:           {len(failed)}")
    print(f"⏭️ Skipped:          {skipped_count} (already exist)")
    print()
    
    if created_count > 0:
        print("🎉 All routers created successfully!")
        print("   They should now appear in Splynx -> Networking -> Hardware -> List")
    else:
        print("⚠️ No routers were created. Check the errors above.")

if __name__ == "__main__":
    main()
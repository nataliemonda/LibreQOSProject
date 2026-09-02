"""
create_remaining_83_routers.py
Create the remaining 83 routers in the correct location (Hardware → List)
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
API_SECRET = "da33ebb5105db0fd254c52e279b23931"  # Replace with your actual secret

# Input files
REGION_MAP_FILE = 'region_map.csv'
ROUTER_CONTENTIONS_FILE = 'router_contentions.csv'
MISSING_MONITORING_FILE = 'missing_monitoring.csv'

# Output files
RESULTS_FILE = 'remaining_83_router_results.csv'
FAILED_FILE = 'remaining_83_router_failed.csv'

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
LOCATION_ID = 2  # Machakos (adjust if needed)

# IP base for new routers
IP_BASE = "10.11.10"

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
    def __init__(self, base_ip="10.11.10"):
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
    print("CREATE REMAINING 83 ROUTERS")
    print("=" * 70)
    print()
    
    # 1. Get all routers that should exist (from router_contentions)
    print("📂 Loading router contentions...")
    print("-" * 50)
    router_contentions = load_csv(ROUTER_CONTENTIONS_FILE)
    print()
    
    if not router_contentions:
        print("❌ No router contentions found!")
        return
    
    # 2. Get existing routers from region_map (38 that already existed)
    region_map = load_csv(REGION_MAP_FILE)
    existing_router_titles = set()
    for row in region_map:
        title = row.get('router_title', '').strip()
        if title:
            existing_router_titles.add(title)
    
    print(f"📋 Found {len(existing_router_titles)} routers from region_map (already existed)")
    print()
    
    # 3. Get all unique router titles from router_contentions
    all_router_titles = set()
    for device in router_contentions:
        title = device.get('title', '').strip()
        if not title:
            continue
        
        # Check if this is a router (contains BRASS, BRAS, IPOE, etc.)
        is_router = any(keyword in title.upper() for keyword in ['BRASS', 'BRAS', 'IPOE'])
        if is_router:
            all_router_titles.add(title)
    
    print(f"📊 Found {len(all_router_titles)} unique router titles from contentions")
    print()
    
    # 4. Get existing monitoring devices
    print("📡 Fetching existing monitoring devices...")
    print("-" * 50)
    monitoring = get_monitoring_devices()
    monitoring_titles = set()
    
    for device in monitoring:
        title = device.get('title', '')
        if title:
            monitoring_titles.add(title.strip())
    
    print(f"✅ Found {len(monitoring)} monitoring devices")
    print()
    
    # 5. Find routers that need to be created
    # These are routers in contentions that are NOT in region_map AND NOT in monitoring
    routers_to_create = []
    
    for title in all_router_titles:
        # Skip if it's already in region_map (already existed)
        if title in existing_router_titles:
            continue
        
        # Skip if it's already in monitoring
        if title in monitoring_titles:
            continue
        
        # Extract region from title (first part before underscore)
        parts = title.split('_')
        region = parts[0] if parts else 'UNKNOWN'
        
        routers_to_create.append({
            'title': title,
            'region': region
        })
    
    print(f"📊 Summary:")
    print(f"   Total routers from contentions: {len(all_router_titles)}")
    print(f"   Already in region_map (skipped): {len(existing_router_titles)}")
    print(f"   Already in monitoring (skipped): {len([t for t in all_router_titles if t in monitoring_titles])}")
    print(f"   Need to create: {len(routers_to_create)}")
    print()
    
    if not routers_to_create:
        print("✅ All routers already exist!")
        return
    
    # Show first 10
    print("📋 First 10 routers to create:")
    print("-" * 50)
    for r in routers_to_create[:10]:
        print(f"   - {r['title']} ({r['region']})")
    if len(routers_to_create) > 10:
        print(f"   ... and {len(routers_to_create) - 10} more")
    print()
    
    # 6. Confirm
    confirm = input(f"⚠️  Create {len(routers_to_create)} routers in the correct location? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Creating routers in Hardware → List...")
    print("=" * 70)
    print()
    
    # 7. Create routers
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
    print(f"✅ Routers created in correct location: {created_count}")
    print(f"❌ Failed: {len(failed)}")
    print(f"   Total remaining to create: {len(routers_to_create)}")
    print()
    
    if created_count > 0:
        print(f"🎉 {created_count} routers created in the correct location!")
        print("   They should now appear in Splynx -> Networking -> Hardware -> List")
    else:
        print("⚠️ No routers were created. Check the errors above.")

if __name__ == "__main__":
    main()
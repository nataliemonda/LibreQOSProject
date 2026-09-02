"""
create_remaining_access_devices.py
Create remaining access devices (skip already created ones)
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
API_SECRET = "b36dbfa127c12d1386f15916d84de80a"  # Replace with your actual secret

# Input files
MISSING_DEVICES_FILE = 'missing_monitoring.csv'
REGION_MAP_FILE = 'region_map.csv'

# Output files
RESULTS_FILE = 'access_device_creation_results.csv'
FAILED_FILE = 'access_device_creation_failed.csv'

# Default values
DEFAULT_PRODUCER = 1
DEFAULT_SNMP_PORT = 161
DEFAULT_SNMP_COMMUNITY = "public"
DEFAULT_SNMP_VERSION = 2
DEFAULT_TYPE = 5  # Access Point
DEFAULT_ACTIVE = 1
DEFAULT_SEND_NOTIFICATIONS = 0
DEFAULT_IS_PING = 1
DEFAULT_MONITORING_GROUP = 1
LOCATION_ID = 2  # Default location

# IP base for new access devices
IP_BASE = "10.11.12"

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
    def __init__(self, base_ip="10.11.12"):
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
    print("CREATE REMAINING ACCESS DEVICES")
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
    
    # 2. Get existing monitoring devices
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
    
    # 3. Filter devices to create (skip already existing)
    devices_to_create = []
    skipped_count = 0
    
    for device in missing_devices:
        title = device.get('title', '').strip()
        region = device.get('region', '')
        
        if not title:
            continue
        
        # Skip if already exists
        if title in existing_titles:
            skipped_count += 1
            continue
        
        # Get region from title if not present
        if not region:
            parts = title.split('_')
            region = parts[0] if parts else 'UNKNOWN'
        
        devices_to_create.append({
            'title': title,
            'region': region,
            'router_id': device.get('router_id', ''),
            'id': device.get('id', '')
        })
    
    print(f"📊 Summary:")
    print(f"   Total missing devices: {len(missing_devices)}")
    print(f"   Already exist (skipped): {skipped_count}")
    print(f"   Need to create: {len(devices_to_create)}")
    print()
    
    if not devices_to_create:
        print("✅ All access devices already exist!")
        return
    
    # Show sample
    print("📋 First 10 devices to create:")
    print("-" * 50)
    for d in devices_to_create[:10]:
        print(f"   - {d['title']} ({d['region']})")
    if len(devices_to_create) > 10:
        print(f"   ... and {len(devices_to_create) - 10} more")
    print()
    
    # 4. Confirm
    confirm = input(f"⚠️  Create {len(devices_to_create)} access devices? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Creating access devices...")
    print("=" * 70)
    print()
    
    # 5. Create devices
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
        
        time.sleep(0.3)
    
    print()
    print(f"✅ Access devices created: {created_count}/{len(devices_to_create)}")
    
    # 6. Save results
    print()
    print("💾 Saving results...")
    print("-" * 50)
    
    if results:
        save_csv(RESULTS_FILE, results, 
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Status', 'Response', 'Timestamp'])
    
    if failed:
        save_csv(FAILED_FILE, failed,
                ['Region', 'Device_Title', 'IP', 'Location_ID', 'Status', 'Response', 'Timestamp'])
    
    # 7. Summary
    print()
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"✅ Access devices created: {created_count}")
    print(f"❌ Failed: {len(failed)}")
    print(f"⏭️ Already existed: {skipped_count}")
    print(f"📋 Total remaining: {len(devices_to_create)}")
    print()
    
    if created_count > 0:
        print(f"🎉 {created_count} access devices created!")
        print("   They should now appear in Splynx -> Networking -> Hardware -> List")
    else:
        print("⚠️ No access devices were created. Check the errors above.")

if __name__ == "__main__":
    main()
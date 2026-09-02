"""
create_missing_parents.py
Fetches existing devices and only creates missing ones.
Skips routers that already exist, creates only missing switches.
"""

import requests
from requests.auth import HTTPBasicAuth
import csv
import time
import json
from datetime import datetime

# ============================================
# CONFIGURATION - UPDATE THESE!
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "6b16484d021797bb5be96ffa58ff1a43"        # Replace with your actual key
API_SECRET = "01bbb20c855712e65c4ab523eaa250b4"  # Replace with your actual secret

# Input file
PARENT_PLAN_FILE = 'parent_creation_plan.csv'

# Output files
RESULTS_FILE = 'missing_creation_results.csv'

# IP address range for new devices
IP_BASE = "10.11.2"  # Changed to avoid conflicts

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

def get_existing_devices():
    """Fetch existing monitoring devices from Splynx"""
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring"
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Found {len(devices)} existing monitoring devices")
            return devices
        else:
            print(f"❌ Failed to fetch devices: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching devices: {str(e)}")
        return []

def create_monitoring_device(device_data, ip_generator):
    """
    Create a monitoring device (switch or access point) in Splynx
    """
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring"
    
    ip = ip_generator.get_next_ip()
    title = device_data.get('Device_Title', '')
    region = device_data.get('Region', '')
    parent_type = device_data.get('Parent_Type', '')
    
    # Determine device type
    # type 2 = switch, type 5 = access point (from monitoring_devices.csv)
    device_type = "2" if parent_type == "Switch" else "5"
    
    payload = {
        "title": title,
        "ip": ip,
        "type": device_type,
        "producer": 1,  # MikroTik
        "active": 1,
        "model": "",
        "location_id": 0,
        "snmp_port": 161,
        "snmp_community": "public",
        "snmp_version": 2,
        "monitoring_group": 1,
    }
    
    print(f"   ({title} -> {ip})", end=" ")
    
    try:
        response = requests.post(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            return True, response.json(), None
        else:
            return False, None, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, None, str(e)

# ============================================
# IP GENERATOR
# ============================================

class IPGenerator:
    def __init__(self, base_ip="10.11.2"):
        self.base = base_ip
        self.counter = 1
    
    def get_next_ip(self):
        ip = f"{self.base}.{self.counter}"
        self.counter += 1
        return ip

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    print("=" * 70)
    print("CREATE MISSING PARENTS (SKIP EXISTING)")
    print("=" * 70)
    print()
    
    # 1. Load parent plan
    print("📂 Loading parent creation plan...")
    print("-" * 50)
    parent_plan = load_csv(PARENT_PLAN_FILE)
    print()
    
    if not parent_plan:
        print("❌ No parent plan found.")
        return
    
    # 2. Fetch existing devices
    print("📡 Fetching existing monitoring devices...")
    print("-" * 50)
    existing_devices = get_existing_devices()
    print()
    
    if not existing_devices:
        print("⚠️ Could not fetch existing devices. Proceeding with caution...")
        existing_titles = set()
    else:
        existing_titles = set()
        for device in existing_devices:
            title = device.get('title', '')
            if title:
                existing_titles.add(title.strip())
        print(f"📋 Found {len(existing_titles)} existing device titles")
    print()
    
    # 3. Filter devices to create (skip existing)
    devices_to_create = []
    skipped_count = 0
    
    for device in parent_plan:
        title = device.get('Device_Title', '').strip()
        region = device.get('Region', '')
        parent_type = device.get('Parent_Type', '')
        
        if not title:
            continue
        
        if title in existing_titles:
            print(f"⏭️ Skipping: {title} ({region}) - already exists")
            skipped_count += 1
            continue
        
        devices_to_create.append(device)
    
    print()
    print(f"📊 Summary:")
    print(f"   Total devices in plan: {len(parent_plan)}")
    print(f"   Already exist (skipped): {skipped_count}")
    print(f"   Need to create: {len(devices_to_create)}")
    print()
    
    if not devices_to_create:
        print("✅ All devices already exist! Nothing to create.")
        return
    
    # 4. Confirm before proceeding
    confirm = input(f"⚠️  Create {len(devices_to_create)} devices? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Starting creation...")
    print("=" * 70)
    print()
    
    # 5. Create devices
    ip_generator = IPGenerator(IP_BASE)
    results = []
    failed = []
    created_count = 0
    
    print("📡 Creating missing devices...")
    print("-" * 50)
    
    for device in devices_to_create:
        region = device.get('Region', 'Unknown')
        title = device.get('Device_Title', 'Unknown')
        parent_type = device.get('Parent_Type', '')
        
        print(f"   Creating {parent_type}: {title} ({region})...", end=" ")
        
        success, response, error = create_monitoring_device(device, ip_generator)
        
        result = {
            'Region': region,
            'Parent_Type': parent_type,
            'Device_Title': title,
            'Status': 'SUCCESS' if success else 'FAILED',
            'Response': str(response) if success else error,
            'Timestamp': datetime.now().isoformat()
        }
        results.append(result)
        
        if success:
            created_count += 1
            print("✅ SUCCESS")
        else:
            failed.append(result)
            print(f"❌ FAILED: {error}")
        
        time.sleep(0.5)
    
    # 6. Save results
    print()
    print("💾 Saving results...")
    print("-" * 50)
    
    if results:
        save_csv(RESULTS_FILE, results, 
                ['Region', 'Parent_Type', 'Device_Title', 'Status', 'Response', 'Timestamp'])
    
    # 7. Summary
    print()
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"✅ Created:  {created_count}/{len(devices_to_create)}")
    print(f"❌ Failed:   {len(failed)}")
    print(f"⏭️ Skipped:  {skipped_count} (already exist)")
    print()
    
    if failed:
        print("❌ Failed devices:")
        for f in failed:
            print(f"   - {f['Device_Title']} ({f['Region']}): {f['Response'][:100]}...")
    
    print()
    print("=" * 70)
    print("📋 Next Steps:")
    print("1. Check missing_creation_results.csv")
    print("2. Verify devices in Splynx dashboard")
    print("3. Run hierarchy_analyzer.py to confirm")
    print("=" * 70)

if __name__ == "__main__":
    main()
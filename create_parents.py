"""
create_parents.py
Creates all missing parent devices (routers and switches) in Splynx.
Reads parent_creation_plan.csv and creates devices via API.
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
API_KEY = "API Key"        # Replace with your actual key
API_SECRET = "Secret API"  # Replace with your actual secret

# Input file
PARENT_PLAN_FILE = 'parent_creation_plan.csv'

# Output files
RESULTS_FILE = 'parent_creation_results.csv'
FAILED_FILE = 'parent_creation_failed.csv'

# IP address range for new devices
IP_BASE = "10.11.1"

# Producer ID (1 = MikroTik, adjust as needed)
PRODUCER_ID = 1

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
# IP GENERATOR
# ============================================

class IPGenerator:
    """Generate sequential IP addresses for new devices"""
    def __init__(self, base_ip="10.11.1"):
        self.base = base_ip
        self.counter = 1
    
    def get_next_ip(self):
        """Get next IP address in sequence (full IPv4 format)"""
        ip = f"{self.base}.{self.counter}"
        self.counter += 1
        return ip

# ============================================
# API FUNCTIONS
# ============================================

def create_router(device_data, ip_generator):
    """
    Create a router in Splynx
    Returns: (success, response_data, error_message)
    """
    endpoint = f"{API_BASE_URL}/admin/networking/routers"
    
    # Generate IP address
    ip = ip_generator.get_next_ip()
    title = device_data.get('Device_Title', '')
    
    payload = {
        "title": title,
        "ip": ip,
        "type": "router",
        "producer": PRODUCER_ID,
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

def create_switch(device_data, ip_generator):
    """
    Create a switch in Splynx using the monitoring endpoint
    Returns: (success, response_data, error_message)
    """
    # Switches are created through the monitoring endpoint
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring"
    
    # Generate IP address
    ip = ip_generator.get_next_ip()
    title = device_data.get('Device_Title', '')
    
    # Build payload for monitoring device (switch)
    payload = {
        "title": title,
        "ip": ip,
        "type": "2",  # type 2 = switch (based on monitoring_devices.csv)
        "producer": PRODUCER_ID,
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

def create_device(device_data, ip_generator):
    """
    Create a device based on parent_type
    Returns: (success, response_data, error_message)
    """
    parent_type = device_data.get('Parent_Type', '')
    
    if parent_type == 'Router':
        return create_router(device_data, ip_generator)
    elif parent_type == 'Switch':
        return create_switch(device_data, ip_generator)
    else:
        return False, None, f"Unknown parent type: {parent_type}"

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    print("=" * 70)
    print("SPLYNX PARENT DEVICE CREATION")
    print("=" * 70)
    print()
    
    # 1. Load parent plan
    print("📂 Loading parent creation plan...")
    print("-" * 50)
    parent_plan = load_csv(PARENT_PLAN_FILE)
    print()
    
    if not parent_plan:
        print("❌ No parent plan found. Please run generate_parent_plan.py first.")
        return
    
    # 2. Confirm API configuration
    print("🔑 API Configuration:")
    print("-" * 50)
    print(f"   API Base URL: {API_BASE_URL}")
    print(f"   API Key: {'*' * 8}... (hidden)")
    print(f"   API Secret: {'*' * 8}... (hidden)")
    print()
    print(f"📋 Device Settings:")
    print(f"   IP Base: {IP_BASE}")
    print(f"   NAS Type: 10 (integer)")
    print(f"   Producer ID: {PRODUCER_ID}")
    print()
    print("⚠️  Switches will be created via the monitoring endpoint")
    print()
    
    # 3. Count devices
    routers = [d for d in parent_plan if d.get('Parent_Type') == 'Router']
    switches = [d for d in parent_plan if d.get('Parent_Type') == 'Switch']
    
    print(f"📊 Devices to create:")
    print(f"   Routers: {len(routers)}")
    print(f"   Switches: {len(switches)}")
    print(f"   Total: {len(parent_plan)}")
    print()
    
    # 4. Confirm before proceeding
    confirm = input(f"⚠️  Are you sure you want to create {len(parent_plan)} devices? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Creation cancelled.")
        return
    
    print()
    print("🚀 Starting creation...")
    print("=" * 70)
    print()
    
    # 5. Initialize IP generator
    ip_generator = IPGenerator(IP_BASE)
    
    # 6. Create devices
    results = []
    failed = []
    created_routers = 0
    created_switches = 0
    
    # Create routers first
    print("📡 Creating Routers...")
    print("-" * 50)
    
    for device in routers:
        region = device.get('Region', 'Unknown')
        title = device.get('Device_Title', 'Unknown')
        
        print(f"   Creating router: {title} ({region})...", end=" ")
        
        success, response, error = create_device(device, ip_generator)
        
        result = {
            'Region': region,
            'Parent_Type': 'Router',
            'Device_Title': title,
            'Status': 'SUCCESS' if success else 'FAILED',
            'Response': str(response) if success else error,
            'Timestamp': datetime.now().isoformat()
        }
        results.append(result)
        
        if success:
            created_routers += 1
            print("✅ SUCCESS")
        else:
            failed.append(result)
            print(f"❌ FAILED: {error}")
        
        time.sleep(0.5)
    
    print()
    print(f"✅ Routers created: {created_routers}/{len(routers)}")
    print()
    
    # Create switches second
    print("🔌 Creating Switches...")
    print("-" * 50)
    print("   (Using monitoring endpoint: /admin/networking/monitoring)")
    print()
    
    for device in switches:
        region = device.get('Region', 'Unknown')
        title = device.get('Device_Title', 'Unknown')
        
        print(f"   Creating switch: {title} ({region})...", end=" ")
        
        success, response, error = create_device(device, ip_generator)
        
        result = {
            'Region': region,
            'Parent_Type': 'Switch',
            'Device_Title': title,
            'Status': 'SUCCESS' if success else 'FAILED',
            'Response': str(response) if success else error,
            'Timestamp': datetime.now().isoformat()
        }
        results.append(result)
        
        if success:
            created_switches += 1
            print("✅ SUCCESS")
        else:
            failed.append(result)
            print(f"❌ FAILED: {error}")
        
        time.sleep(0.5)
    
    print()
    print(f"✅ Switches created: {created_switches}/{len(switches)}")
    print()
    
    # 7. Save results
    print("💾 Saving results...")
    print("-" * 50)
    
    if results:
        save_csv(RESULTS_FILE, results, 
                ['Region', 'Parent_Type', 'Device_Title', 'Status', 'Response', 'Timestamp'])
    
    if failed:
        save_csv(FAILED_FILE, failed,
                ['Region', 'Parent_Type', 'Device_Title', 'Status', 'Response', 'Timestamp'])
    
    # 8. Summary
    print()
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"✅ Routers created:  {created_routers}/{len(routers)}")
    print(f"✅ Switches created: {created_switches}/{len(switches)}")
    print(f"✅ Total created:    {created_routers + created_switches}/{len(parent_plan)}")
    print(f"❌ Failed:           {len(failed)}")
    print()
    
    if failed:
        print("❌ Failed devices (showing first 5):")
        for f in failed[:5]:
            print(f"   - {f['Device_Title']} ({f['Region']}): {f['Response'][:150]}...")
        if len(failed) > 5:
            print(f"   ... and {len(failed) - 5} more")
    
    print()
    print("=" * 70)
    print("📋 Next Steps:")
    print("1. Review parent_creation_results.csv")
    print("2. Check parent_creation_failed.csv for errors")
    print("3. Once all parents exist, run hierarchy_analyzer.py again")
    print("4. Then run the access device creation script")
    print("=" * 70)

if __name__ == "__main__":
    main()

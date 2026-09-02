"""
check_devices.py
Check if created devices exist in Splynx and their current status
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

API_BASE_URL = "https://home.mawingunetworks.com/api/2.0"
API_KEY = "6b16484d021797bb5be96ffa58ff1a43"        # Replace with your actual key
API_SECRET = "01bbb20c855712e65c4ab523eaa250b4"  # Replace with your actual secret

# ============================================
# FUNCTIONS
# ============================================

def get_monitoring_devices():
    """Fetch all monitoring devices from Splynx"""
    endpoint = f"{API_BASE_URL}/admin/networking/monitoring"
    
    print(f"📡 Fetching monitoring devices from: {endpoint}")
    print("-" * 50)
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Found {len(devices)} monitoring devices")
            return devices
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return []

def get_routers():
    """Fetch all routers from Splynx"""
    endpoint = f"{API_BASE_URL}/admin/networking/routers"
    
    print(f"\n📡 Fetching routers from: {endpoint}")
    print("-" * 50)
    
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            routers = response.json()
            print(f"✅ Found {len(routers)} routers")
            return routers
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return []

def search_devices(devices, search_terms):
    """Search for specific devices by title"""
    results = []
    
    for device in devices:
        title = device.get('title', '')
        device_id = device.get('id', '')
        device_type = device.get('type', '')
        ip = device.get('ip', '')
        
        for term in search_terms:
            if term.lower() in title.lower():
                results.append({
                    'id': device_id,
                    'title': title,
                    'type': device_type,
                    'ip': ip,
                    'active': device.get('active', ''),
                    'location_id': device.get('location_id', ''),
                    'parent_id': device.get('parent_id', ''),
                })
                break
    
    return results

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("CHECK CREATED DEVICES")
    print("=" * 70)
    print()
    
    # 1. Get all devices
    monitoring_devices = get_monitoring_devices()
    routers = get_routers()
    
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total monitoring devices: {len(monitoring_devices)}")
    print(f"Total routers:            {len(routers)}")
    print()
    
    # 2. Search for recently created devices
    search_terms = ["ABCP", "ABCT", "AMAL", "BAHN", "BARP"]
    
    print("🔍 Searching for recently created devices...")
    print("-" * 50)
    
    # Search in monitoring devices
    monitoring_results = search_devices(monitoring_devices, search_terms)
    
    if monitoring_results:
        print(f"\n✅ Found {len(monitoring_results)} devices in monitoring:")
        for device in monitoring_results[:10]:  # Show first 10
            print(f"   - {device['title']} (ID: {device['id']}, Type: {device['type']}, IP: {device['ip']})")
        if len(monitoring_results) > 10:
            print(f"   ... and {len(monitoring_results) - 10} more")
    else:
        print("\n❌ No recently created devices found in monitoring")
    
    # Search in routers
    router_results = search_devices(routers, search_terms)
    
    if router_results:
        print(f"\n✅ Found {len(router_results)} devices in routers:")
        for device in router_results[:10]:
            print(f"   - {device['title']} (ID: {device['id']}, IP: {device['ip']})")
        if len(router_results) > 10:
            print(f"   ... and {len(router_results) - 10} more")
    else:
        print("\n❌ No recently created devices found in routers")
    
    # 3. Show sample of what's in monitoring
    print("\n" + "=" * 70)
    print("📋 Sample of existing monitoring devices (first 5):")
    print("=" * 70)
    for device in monitoring_devices[:5]:
        print(f"   - {device.get('title', '')} (Type: {device.get('type', '')}, IP: {device.get('ip', '')})")
    
    # 4. Try to find any device with 10.11.2.x IP
    print("\n" + "=" * 70)
    print("🔍 Searching for devices with IP 10.11.2.x...")
    print("=" * 70)
    
    found_ips = []
    for device in monitoring_devices:
        ip = device.get('ip', '')
        if ip and ip.startswith('10.11.2.'):
            found_ips.append({
                'title': device.get('title', ''),
                'ip': ip,
                'type': device.get('type', ''),
                'id': device.get('id', '')
            })
    
    if found_ips:
        print(f"✅ Found {len(found_ips)} devices with IP 10.11.2.x:")
        for device in found_ips[:10]:
            print(f"   - {device['title']} (IP: {device['ip']}, Type: {device['type']})")
        if len(found_ips) > 10:
            print(f"   ... and {len(found_ips) - 10} more")
    else:
        print("❌ No devices found with IP 10.11.2.x")
        print("   This means the devices were NOT created successfully,")
        print("   or they were created but have different IPs.")

if __name__ == "__main__":
    main()
"""
hierarchy_analyzer.py
Analyzes Splynx hierarchy and generates reports
Input: router_contentions.csv, monitoring_devices.csv, region_map.csv
Output: Various CSV reports
"""

import csv
import re
from collections import defaultdict

# ============================================
# CONFIGURATION
# ============================================

ROUTER_CONTENTIONS_FILE = 'router_contentions.csv'
MONITORING_DEVICES_FILE = 'monitoring_devices.csv'
REGION_MAP_FILE = 'region_map.csv'

# ============================================
# HELPER FUNCTIONS
# ============================================

def extract_region(title):
    """Extract region code from device title (first part before underscore)"""
    if not title:
        return None
    parts = title.split('_')
    return parts[0] if parts else None

def classify_device_type(title):
    """
    Classify device type based on naming convention
    Returns: 'router', 'switch', 'access_point', 'unknown'
    """
    if not title:
        return 'unknown'
    
    title_upper = title.upper()
    
    # Routers: contain BRASS, BRAS, IPoE, etc.
    router_keywords = ['BRASS', 'BRAS', 'IPOE', 'BRAS_IPOE', 'BRASS_IPOE']
    if any(keyword in title_upper for keyword in router_keywords):
        return 'router'
    
    # Switches: contain SW, _SW_
    if '_SW_' in title_upper or title_upper.endswith('_SW') or '_SW' in title_upper:
        return 'switch'
    
    # Access Points: contain SEC, SYH, HORN, ASYH, etc.
    access_keywords = ['SEC', 'SYH', 'HORN', 'ASYH', 'PTP', 'PTMP', '_AP']
    if any(keyword in title_upper for keyword in access_keywords):
        return 'access_point'
    
    return 'unknown'

def load_csv(filename):
    """Load CSV and return list of dicts with cleaned keys"""
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # Read first line to detect delimiter
            first_line = f.readline()
            f.seek(0)
            
            # Try comma first, then tab
            delimiter = ',' if ',' in first_line else '\t'
            
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                # Clean keys (remove whitespace, BOM, etc.)
                clean_row = {}
                for key, value in row.items():
                    clean_key = key.strip().replace('\ufeff', '')
                    clean_row[clean_key] = value.strip() if value else ''
                data.append(clean_row)
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
# STEP 1: BUILD HIERARCHY FROM MONITORING
# ============================================

def build_hierarchy(monitoring_devices):
    """
    Build hierarchy from monitoring devices
    Returns: dict with region -> {router, switches, access_points}
    """
    hierarchy = defaultdict(lambda: {
        'router': None,
        'router_id': None,
        'switches': [],
        'switch_ids': [],
        'access_points': [],
        'access_point_ids': [],
        'all_devices': []
    })
    
    for device in monitoring_devices:
        title = device.get('title', '')
        device_id = device.get('id', '')
        region = extract_region(title)
        device_type = classify_device_type(title)
        
        if not region:
            continue
        
        if device_type == 'router':
            if hierarchy[region]['router'] is None:
                hierarchy[region]['router'] = title
                hierarchy[region]['router_id'] = device_id
        elif device_type == 'switch':
            hierarchy[region]['switches'].append(title)
            hierarchy[region]['switch_ids'].append(device_id)
        elif device_type == 'access_point':
            hierarchy[region]['access_points'].append(title)
            hierarchy[region]['access_point_ids'].append(device_id)
        
        hierarchy[region]['all_devices'].append({
            'title': title,
            'id': device_id,
            'type': device_type
        })
    
    return hierarchy

# ============================================
# STEP 2: ANALYZE MISSING DEVICES
# ============================================

def find_missing_devices(router_contentions, monitoring_devices, hierarchy):
    """
    Find devices in router_contentions that are NOT in monitoring_devices
    """
    # Create set of existing device titles (from monitoring)
    existing_titles = set()
    for device in monitoring_devices:
        title = device.get('title', '')
        if title:
            existing_titles.add(title.strip())
    
    # Find missing devices
    missing = []
    for device in router_contentions:
        title = device.get('title', '')
        if not title:
            continue
        
        # Clean title
        title_clean = title.strip()
        
        if title_clean not in existing_titles:
            missing.append({
                'id': device.get('id', ''),
                'router_id': device.get('router_id', ''),
                'title': title_clean,
                'speed_down': device.get('speed_down', ''),
                'speed_up': device.get('speed_up', ''),
                'limit_at': device.get('limit_at', ''),
                'region': extract_region(title_clean),
                'device_type': classify_device_type(title_clean)
            })
    
    return missing

# ============================================
# STEP 3: GENERATE REPORTS
# ============================================

def generate_reports(missing_devices, hierarchy, region_map):
    """
    Generate all analysis reports
    """
    
    # --- Report 1: Missing Parents ---
    # Devices that are blocked because parent router or switch is missing
    missing_parents = []
    ready_for_creation = []
    region_status = []
    
    for device in missing_devices:
        region = device['region']
        if not region:
            continue
        
        # Check if region has router
        has_router = hierarchy.get(region, {}).get('router') is not None
        has_switch = len(hierarchy.get(region, {}).get('switches', [])) > 0
        
        # Get router title from region_map if available
        router_title = None
        for row in region_map:
            if row.get('region') == region:
                router_title = row.get('router_title')
                break
        
        if not has_router:
            # Missing router
            missing_parents.append({
                'id': device['id'],
                'router_id': device['router_id'],
                'title': device['title'],
                'region': region,
                'missing': 'Router',
                'router_title': router_title or 'Unknown'
            })
        elif not has_switch:
            # Has router but no switch
            missing_parents.append({
                'id': device['id'],
                'router_id': device['router_id'],
                'title': device['title'],
                'region': region,
                'missing': 'Switch',
                'router_title': router_title or 'Unknown'
            })
        else:
            # Ready for creation (has both router and switch)
            ready_for_creation.append({
                'router': hierarchy[region]['router'],
                'router_id': hierarchy[region]['router_id'],
                'switch': hierarchy[region]['switches'][0] if hierarchy[region]['switches'] else '',
                'switch_id': hierarchy[region]['switch_ids'][0] if hierarchy[region]['switch_ids'] else '',
                'missing_device': device['title'],
                'router_contention_id': device['id']
            })
    
    # --- Report 2: Region Status ---
    all_regions = set()
    for device in missing_devices:
        if device['region']:
            all_regions.add(device['region'])
    
    for region in sorted(all_regions):
        has_router = hierarchy.get(region, {}).get('router') is not None
        has_switch = len(hierarchy.get(region, {}).get('switches', [])) > 0
        
        if has_router and has_switch:
            status = 'COMPLETE'
        elif has_router and not has_switch:
            status = 'NEEDS_SWITCH'
        elif not has_router and has_switch:
            status = 'NEEDS_ROUTER'
        else:
            status = 'NEEDS_BOTH'
        
        region_status.append({
            'Family': region,
            'Router': hierarchy.get(region, {}).get('router') or 'MISSING',
            'Switch': hierarchy.get(region, {}).get('switches', ['MISSING'])[0] if hierarchy.get(region, {}).get('switches') else 'MISSING',
            'Status': status,
            'Missing_Devices': len([d for d in missing_devices if d['region'] == region])
        })
    
    return missing_parents, ready_for_creation, region_status

# ============================================
# STEP 4: GENERATE SUMMARY STATISTICS
# ============================================

def generate_summary(missing_devices, missing_parents, ready_for_creation, region_status, hierarchy):
    """Generate summary statistics"""
    
    total_missing = len(missing_devices)
    blocked = len(missing_parents)
    ready = len(ready_for_creation)
    
    regions_needing_both = [r for r in region_status if r['Status'] == 'NEEDS_BOTH']
    regions_needing_router = [r for r in region_status if r['Status'] == 'NEEDS_ROUTER']
    regions_needing_switch = [r for r in region_status if r['Status'] == 'NEEDS_SWITCH']
    regions_complete = [r for r in region_status if r['Status'] == 'COMPLETE']
    
    summary = {
        'total_missing_devices': total_missing,
        'blocked_devices': blocked,
        'ready_for_creation': ready,
        'regions_needing_both': len(regions_needing_both),
        'regions_needing_router': len(regions_needing_router),
        'regions_needing_switch': len(regions_needing_switch),
        'regions_complete': len(regions_complete),
        'total_regions': len(region_status)
    }
    
    return summary

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    print("=" * 70)
    print("SPLYNX HIERARCHY ANALYZER")
    print("=" * 70)
    print()
    
    # 1. Load data
    print("📂 Loading data...")
    print("-" * 50)
    
    router_contentions = load_csv(ROUTER_CONTENTIONS_FILE)
    monitoring_devices = load_csv(MONITORING_DEVICES_FILE)
    region_map = load_csv(REGION_MAP_FILE)
    
    if not router_contentions or not monitoring_devices:
        print("❌ Cannot proceed without data files.")
        return
    
    print()
    
    # 2. Build hierarchy from monitoring
    print("🏗️ Building hierarchy from monitoring devices...")
    print("-" * 50)
    hierarchy = build_hierarchy(monitoring_devices)
    print(f"✅ Found {len(hierarchy)} regions in monitoring data")
    print()
    
    # 3. Find missing devices
    print("🔍 Finding missing devices...")
    print("-" * 50)
    missing_devices = find_missing_devices(router_contentions, monitoring_devices, hierarchy)
    print(f"✅ Found {len(missing_devices)} missing devices")
    print()
    
    # 4. Generate reports
    print("📊 Generating reports...")
    print("-" * 50)
    missing_parents, ready_for_creation, region_status = generate_reports(
        missing_devices, hierarchy, region_map
    )
    print()
    
    # 5. Save reports
    print("💾 Saving reports...")
    print("-" * 50)
    
    # Save missing devices (full list)
    if missing_devices:
        save_csv('missing_monitoring.csv', missing_devices, 
                ['id', 'router_id', 'title', 'speed_down', 'speed_up', 'limit_at', 'region', 'device_type'])
    
    # Save missing parents report
    if missing_parents:
        save_csv('report_missing_parents.csv', missing_parents,
                ['id', 'router_id', 'title', 'region', 'missing', 'router_title'])
    
    # Save ready for creation report
    if ready_for_creation:
        save_csv('report_ready_for_creation.csv', ready_for_creation,
                ['router', 'router_id', 'switch', 'switch_id', 'missing_device', 'router_contention_id'])
    else:
        print("⚠️ No devices ready for creation yet (all are blocked by missing parents)")
    
    # Save region status report
    if region_status:
        save_csv('report_region_status.csv', region_status,
                ['Family', 'Router', 'Switch', 'Status', 'Missing_Devices'])
    
    # 6. Generate summary
    print()
    print("=" * 70)
    print("📊 SUMMARY STATISTICS")
    print("=" * 70)
    
    summary = generate_summary(missing_devices, missing_parents, ready_for_creation, region_status, hierarchy)
    
    print(f"Total missing devices:        {summary['total_missing_devices']}")
    print(f"Blocked (missing parent):     {summary['blocked_devices']}")
    print(f"Ready for creation:           {summary['ready_for_creation']}")
    print()
    print(f"Regions needing BOTH:         {summary['regions_needing_both']}")
    print(f"Regions needing ROUTER:       {summary['regions_needing_router']}")
    print(f"Regions needing SWITCH:       {summary['regions_needing_switch']}")
    print(f"Regions COMPLETE:             {summary['regions_complete']}")
    print(f"Total regions analyzed:       {summary['total_regions']}")
    print()
    print("=" * 70)
    print("✅ Analysis complete! Check the CSV files above.")
    print("=" * 70)

if __name__ == "__main__":
    main()
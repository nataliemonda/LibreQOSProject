"""
generate_parent_plan.py
Generates a CSV of all missing parent devices (routers and switches)
that need to be created in Splynx.
Uses correct naming conventions from region_map.csv
"""

import csv
from collections import defaultdict

# ============================================
# CONFIGURATION
# ============================================

REGION_STATUS_FILE = 'report_region_status.csv'
REGION_MAP_FILE = 'region_map.csv'
OUTPUT_FILE = 'parent_creation_plan.csv'

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

# ============================================
# GENERATE PARENT DEVICE NAMES
# ============================================

def generate_router_name(region, region_map):
    """
    Generate router name using naming convention: {COUNTY}_{REGION}_BRASS_IPOE
    If region is in region_map, use the router_title from there.
    """
    # First check if region is in region_map
    for row in region_map:
        if row.get('region', '').strip().upper() == region.upper():
            router_title = row.get('router_title', '')
            if router_title and router_title != 'Unknown':
                return router_title
    
    # If not in region_map, try to find county from region_map
    county = None
    for row in region_map:
        if row.get('region', '').strip().upper() == region.upper():
            county = row.get('county', '').strip()
            break
    
    # If county found, use it
    if county:
        return f"{county}_{region}_BRASS_IPOE"
    
    # Fallback: just use region
    return f"{region}_BRASS_IPOE"

def generate_switch_name(region):
    """Generate switch name using naming convention: {REGION}_SW"""
    # Clean region name (remove spaces, special characters)
    clean_region = region.strip().upper()
    return f"{clean_region}_SW"

def get_parent_type(status):
    """Determine what parent devices are needed based on status"""
    if status == 'NEEDS_ROUTER':
        return ['Router']
    elif status == 'NEEDS_SWITCH':
        return ['Switch']
    elif status == 'NEEDS_BOTH':
        return ['Router', 'Switch']
    else:
        return []

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    print("=" * 70)
    print("PARENT CREATION PLAN GENERATOR")
    print("=" * 70)
    print()
    
    # 1. Load data
    print("📂 Loading data...")
    print("-" * 50)
    region_status = load_csv(REGION_STATUS_FILE)
    region_map = load_csv(REGION_MAP_FILE)
    print()
    
    if not region_status:
        print("❌ No region status data found. Please run hierarchy_analyzer.py first.")
        return
    
    # 2. Display region_map for reference
    print("📋 Region Map Reference:")
    print("-" * 50)
    for row in region_map[:5]:  # Show first 5
        print(f"  {row.get('region')} -> {row.get('county')} -> {row.get('router_title')}")
    if len(region_map) > 5:
        print(f"  ... and {len(region_map) - 5} more")
    print()
    
    # 3. Generate parent creation plan
    print("🏗️ Generating parent creation plan...")
    print("-" * 50)
    
    parent_plan = []
    region_count = 0
    router_count = 0
    switch_count = 0
    regions_with_map = 0
    regions_without_map = 0
    
    for row in region_status:
        region = row.get('Family', '').strip()
        status = row.get('Status', '').strip()
        missing_devices = row.get('Missing_Devices', '0')
        
        if not region:
            continue
            
        # Skip regions that are complete or have no missing devices
        if status == 'COMPLETE' or int(missing_devices) == 0:
            continue
        
        # Check if region is in region_map
        in_map = False
        for r in region_map:
            if r.get('region', '').strip().upper() == region.upper():
                in_map = True
                break
        
        if in_map:
            regions_with_map += 1
        else:
            regions_without_map += 1
        
        # Determine what parents are needed
        parent_types = get_parent_type(status)
        
        for parent_type in parent_types:
            if parent_type == 'Router':
                router_title = generate_router_name(region, region_map)
                
                # Check if this router already exists in region_map
                existing_router = None
                for r in region_map:
                    if r.get('region', '').strip().upper() == region.upper():
                        existing_router = r.get('router_title', '')
                        break
                
                if existing_router and existing_router != 'Unknown':
                    # Router already exists in region_map, skip
                    continue
                
                parent_plan.append({
                    'Region': region,
                    'Parent_Type': 'Router',
                    'Device_Title': router_title,
                    'Status': status,
                    'Missing_Devices': missing_devices,
                    'Notes': f'Create this router first. Naming: {{COUNTY}}_{{REGION}}_BRASS_IPOE'
                })
                router_count += 1
                
            elif parent_type == 'Switch':
                switch_title = generate_switch_name(region)
                
                parent_plan.append({
                    'Region': region,
                    'Parent_Type': 'Switch',
                    'Device_Title': switch_title,
                    'Status': status,
                    'Missing_Devices': missing_devices,
                    'Notes': 'Create this switch after router exists. Naming: {REGION}_SW'
                })
                switch_count += 1
        
        region_count += 1
    
    # 4. Save the plan
    print(f"✅ Generated {len(parent_plan)} parent devices to create")
    print(f"   - Routers: {router_count}")
    print(f"   - Switches: {switch_count}")
    print(f"   - Regions in map: {regions_with_map}")
    print(f"   - Regions NOT in map: {regions_without_map}")
    print()
    
    if parent_plan:
        save_csv(OUTPUT_FILE, parent_plan, 
                ['Region', 'Parent_Type', 'Device_Title', 'Status', 'Missing_Devices', 'Notes'])
        print(f"💾 Saved to {OUTPUT_FILE}")
    else:
        print("⚠️ No parent devices need to be created. All regions are complete!")
    
    # 5. Summary
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Regions processed:     {region_count}")
    print(f"Routers to create:     {router_count}")
    print(f"Switches to create:    {switch_count}")
    print(f"Total parent devices:  {len(parent_plan)}")
    print()
    print("📋 Naming Convention:")
    print("   Router: {COUNTY}_{REGION}_BRASS_IPOE  (e.g., MIG_MIGT_BRASS_IPOE)")
    print("   Switch: {REGION}_SW                  (e.g., MIGT_SW)")
    print()
    print("📋 Next Steps:")
    print("1. Review parent_creation_plan.csv")
    print("2. Verify the device names follow your naming convention")
    print("3. Run the parent creation script (next step)")
    print("=" * 70)

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

if __name__ == "__main__":
    main()
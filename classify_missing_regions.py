import csv
import os

# -----------------------------
# Load monitoring devices
# -----------------------------

monitoring = []

with open("monitoring_devices.csv", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        monitoring.append(row)

# -----------------------------
# Load missing monitoring
# -----------------------------

missing = []

with open("missing_monitoring.csv", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        missing.append(row)

# -----------------------------
# Build lookups
# -----------------------------

routers = {}
switches = {}

for device in monitoring:

    title = device["title"].strip()

    # Root routers (BRAS / BRASS)
    if (
        device["parent_id"] == "0"
        and (
            "BRAS" in title.upper()
            or "BRASS" in title.upper()
        )
    ):
        routers[title] = device

    # All switches
    if title.endswith("_SW"):
        switches[title] = device

# -----------------------------
# Find unique families
# -----------------------------

families = {}

for row in missing:

    family = row["title"].split("_")[0]

    if family not in families:
        families[family] = row["title"]

# -----------------------------
# Generate report
# -----------------------------

results = []

for family in sorted(families):

    router_found = False
    router_name = ""

    switch_found = False
    switch_name = ""

    # Look for a router containing the family name
    for router in routers:

        if family in router:

            router_found = True
            router_name = router
            break

    # Look for a switch beginning with the family
    for switch in switches:

        if switch.startswith(family + "_"):

            switch_found = True
            switch_name = switch
            break

    if router_found and switch_found:
        status = "READY_FOR_MONITORING"

    elif router_found:
        status = "MISSING_SWITCH"

    else:
        status = "MISSING_PARENT"

    results.append({
        "Family": family,
        "Router": router_name,
        "Switch": switch_name,
        "Status": status
    })

# -----------------------------
# Save report
# -----------------------------

os.makedirs("reports", exist_ok=True)

with open(
    "reports/report_region_status.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "Family",
            "Router",
            "Switch",
            "Status"
        ]
    )

    writer.writeheader()
    writer.writerows(results)

print()
print("===================================")
print("REGION STATUS REPORT CREATED")
print("===================================")
print(f"Families analysed: {len(results)}")
print("Saved to reports/report_region_status.csv")
import csv
import os
from collections import defaultdict

# -----------------------------
# Load monitoring devices
# -----------------------------

monitoring = []

with open("monitoring_devices.csv", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        monitoring.append(row)

print(f"Loaded {len(monitoring)} monitoring devices.")

# -----------------------------
# Build lookup dictionaries
# -----------------------------

device_by_id = {}
children = defaultdict(list)

for device in monitoring:
    device_by_id[device["id"]] = device
    children[device["parent_id"]].append(device)

# -----------------------------
# Find root routers
# -----------------------------

root_routers = []

for device in monitoring:

    title = device["title"].upper()

    if (
        device["parent_id"] == "0"
        and (
            "BRASS" in title
            or "BRAS" in title
        )
    ):
        root_routers.append(device)

print(f"Found {len(root_routers)} root routers.")

# -----------------------------
# Create reports folder
# -----------------------------

os.makedirs("reports", exist_ok=True)

report = open(
    "reports/hierarchy_report.csv",
    "w",
    newline="",
    encoding="utf-8"
)

writer = csv.writer(report)

writer.writerow([
    "Router",
    "Router ID",
    "Switch",
    "Switch ID",
    "Access Device",
    "Access Device ID"
])

# -----------------------------
# Recursive function
# -----------------------------

def walk_switch(router, switch):

    switch_children = children[switch["id"]]

    for child in switch_children:

        title = child["title"]

        # Another switch
        if title.endswith("_SW"):

            walk_switch(router, child)

        else:

            writer.writerow([
                router["title"],
                router["id"],
                switch["title"],
                switch["id"],
                child["title"],
                child["id"]
            ])

# -----------------------------
# Walk every router
# -----------------------------

for router in root_routers:

    router_children = children[router["id"]]

    for child in router_children:

        if child["title"].endswith("_SW"):

            walk_switch(router, child)

report.close()

print()
print("Hierarchy report generated.")
print("Location: reports/hierarchy_report.csv")
import csv
import os

# -----------------------------
# Load hierarchy report
# -----------------------------

hierarchy = []

with open(
    "reports/hierarchy_report.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        hierarchy.append(row)

print(f"Hierarchy rows loaded: {len(hierarchy)}")

# -----------------------------
# Load missing monitoring
# -----------------------------

missing = []

with open(
    "missing_monitoring.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        missing.append(row)

print(f"Missing monitoring rows: {len(missing)}")

# -----------------------------
# Build family lookup
# -----------------------------

family_lookup = {}

for row in hierarchy:

    access_device = row["Access Device"]

    if not access_device:
        continue

    family = access_device.split("_")[0]

    # Store the first verified mapping
    if family not in family_lookup:

        family_lookup[family] = {

            "Router": row["Router"],
            "Router ID": row["Router ID"],
            "Switch": row["Switch"],
            "Switch ID": row["Switch ID"]

        }

print(f"Families discovered: {len(family_lookup)}")

# -----------------------------
# Create report
# -----------------------------

os.makedirs("reports", exist_ok=True)

ready = []

for row in missing:

    family = row["title"].split("_")[0]

    if family in family_lookup:

        mapping = family_lookup[family]

        ready.append({

            "Router": mapping["Router"],
            "Router ID": mapping["Router ID"],
            "Switch": mapping["Switch"],
            "Switch ID": mapping["Switch ID"],
            "Missing Device": row["title"],
            "Router Contention ID": row["id"]

        })

# -----------------------------
# Save report
# -----------------------------

with open(
    "reports/report_ready_for_creation.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "Router",
        "Router ID",
        "Switch",
        "Switch ID",
        "Missing Device",
        "Router Contention ID"
    ]

    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()

    writer.writerows(ready)

print()
print("=====================================")
print("READY FOR CREATION REPORT GENERATED")
print("=====================================")
print(f"Ready devices: {len(ready)}")
print("Saved to reports/report_ready_for_creation.csv")
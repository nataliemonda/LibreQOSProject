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
# Load router contentions
# -----------------------------

router_contentions = []

with open("router_contentions.csv", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        router_contentions.append(row)

# -----------------------------
# Find all root routers
# -----------------------------

root_router_titles = set()

for device in monitoring:

    title = device["title"].upper()

    if (
        device["parent_id"] == "0"
        and (
            "BRASS" in title
            or "BRAS" in title
        )
    ):

        root_router_titles.add(title)

# -----------------------------
# Create reports folder
# -----------------------------

os.makedirs("reports", exist_ok=True)

# -----------------------------
# Report 1
# -----------------------------

missing = []

for contention in router_contentions:

    prefix = contention["title"].split("_")[0]

    found = False

    for router in root_router_titles:

        if prefix in router:

            found = True
            break

    if not found:

        missing.append(contention)

# -----------------------------
# Save report
# -----------------------------

with open(
    "reports/report_missing_parents.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "id",
        "router_id",
        "title",
        "speed_down",
        "speed_up",
        "limit_at"
    ])

    for row in missing:

        writer.writerow([
            row["id"],
            row["router_id"],
            row["title"],
            row["speed_down"],
            row["speed_up"],
            row["limit_at"]
        ])

print()
print("Report created successfully.")
print("Missing parent regions:", len(missing))
print("Saved to reports/report_missing_parents.csv")
import csv

# ---------------------------------------
# Load router contentions
# ---------------------------------------

router_contentions = []

with open(
    "router_contentions.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        router_contentions.append(row)


# ---------------------------------------
# Load existing monitoring/access devices
# ---------------------------------------

monitoring_titles = set()

with open(
    "monitoring_devices.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        title = row["title"].strip().upper()

        monitoring_titles.add(title)


# ---------------------------------------
# Find router contentions without
# monitoring devices
# ---------------------------------------

missing = []

for contention in router_contentions:

    title = contention["title"].strip()

    if title.upper() not in monitoring_titles:

        missing.append({
            "id": contention["id"],
            "router_id": contention["router_id"],
            "title": title,
            "speed_down": contention["speed_down"],
            "speed_up": contention["speed_up"],
            "limit_at": contention["limit_at"]
        })


# ---------------------------------------
# Create missing_monitoring.csv
# ---------------------------------------

with open(
    "missing_monitoring.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "id",
            "router_id",
            "title",
            "speed_down",
            "speed_up",
            "limit_at"
        ]
    )

    writer.writeheader()

    writer.writerows(missing)


# ---------------------------------------
# Results
# ---------------------------------------

print()
print("======================================")
print("MISSING MONITORING DEVICES GENERATED")
print("======================================")
print()
print("Router contentions:", len(router_contentions))
print("Existing monitoring:", len(monitoring_titles))
print("Missing monitoring:", len(missing))
print()
print("Saved to: missing_monitoring.csv")
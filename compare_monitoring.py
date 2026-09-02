import csv

# Load monitoring titles
monitoring_titles = set()

with open(
    "monitoring_devices.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        monitoring_titles.add(
            row["title"].strip().upper()
        )

# Find missing titles
missing = []

with open(
    "router_contentions.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        title = row["title"].strip().upper()

        if title not in monitoring_titles:

            missing.append(row)

# Save output
with open(
    "missing_monitoring.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=missing[0].keys()
    )

    writer.writeheader()

    writer.writerows(missing)

print("Router contentions without monitoring:", len(missing))
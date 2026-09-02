import csv
import os

mapping = []

with open("monitoring_devices.csv", encoding="utf-8") as file:

    reader = csv.DictReader(file)

    for row in reader:

        title = row["title"].upper()

        if (
            row["parent_id"] == "0"
            and (
                "BRAS" in title
                or "BRASS" in title
            )
        ):

            parts = title.split("_")

            if len(parts) >= 3:

                county = parts[0]
                region = parts[1]

                mapping.append({
                    "region": region,
                    "county": county,
                    "router_title": title
                })

os.makedirs("reports", exist_ok=True)

with open(
    "reports/region_map.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "region",
            "county",
            "router_title"
        ]
    )

    writer.writeheader()
    writer.writerows(mapping)

print()
print("Region map created.")
print(f"Regions found: {len(mapping)}")
print("Saved to reports/region_map.csv")
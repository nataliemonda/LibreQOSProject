import csv

family = input("Enter family: ").strip().upper()

found = False

with open("monitoring_devices.csv", encoding="utf-8") as file:

    reader = csv.DictReader(file)

    for row in reader:

        title = row["title"].upper()

        if family in title:

            found = True

            print(
                row["id"],
                "|",
                row["parent_id"],
                "|",
                row["title"]
            )

if not found:
    print("No devices found.")
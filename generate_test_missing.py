import csv

# Number of test devices you want
NUMBER_OF_DEVICES = 5

with open(
    "missing_monitoring.csv",
    encoding="utf-8"
) as infile:

    reader = csv.DictReader(infile)

    rows = list(reader)

with open(
    "missing_monitoring_test.csv",
    "w",
    newline="",
    encoding="utf-8"
) as outfile:

    writer = csv.DictWriter(
        outfile,
        fieldnames=reader.fieldnames
    )

    writer.writeheader()

    for row in rows[:NUMBER_OF_DEVICES]:
        writer.writerow(row)

print(f"Created missing_monitoring_test.csv with {NUMBER_OF_DEVICES} devices.")
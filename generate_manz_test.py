import csv

FAMILY = "MANZ"
LIMIT = 5

matches = []

with open(
    "missing_monitoring.csv",
    encoding="utf-8"
) as infile:

    reader = csv.DictReader(infile)

    fieldnames = reader.fieldnames

    for row in reader:

        if row["title"].startswith(FAMILY + "_"):

            matches.append(row)

            if len(matches) == LIMIT:
                break

with open(
    "missing_monitoring_test.csv",
    "w",
    newline="",
    encoding="utf-8"
) as outfile:

    writer = csv.DictWriter(
        outfile,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(matches)

print(f"{len(matches)} {FAMILY} devices written to missing_monitoring_test.csv")
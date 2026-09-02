import csv

with open(
    "router_contentions.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        if row["router_id"] == "55":

            print(row["title"])
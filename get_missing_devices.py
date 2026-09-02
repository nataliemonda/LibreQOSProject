import requests
from requests.auth import HTTPBasicAuth
import csv

url = "https://home.mawingunetworks.com/api/2.0/admin/networking/routers-sectors"

key = "API Key"
secret = "Secret API"

response = requests.get(
    url,
    auth=HTTPBasicAuth(
        key,
        secret
    )
)

print(
    "Status:",
    response.status_code
)

if response.status_code == 200:

    data = response.json()

    with open(
        "router_contentions.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=data[0].keys()
        )

        writer.writeheader()

        writer.writerows(data)

    print(
        "Saved router_contentions.csv"
    )

else:

    print(
        response.text
    )

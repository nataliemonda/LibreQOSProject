import requests
from requests.auth import HTTPBasicAuth
import csv

url = "https://home.mawingunetworks.com/api/2.0/admin/networking/monitoring"

key = "API Key"
secret = "Secret API"

response = requests.get(
    url,
    auth=HTTPBasicAuth(key, secret)
)

print("Status:", response.status_code)

if response.status_code == 200:

    data = response.json()

    if len(data) > 0:

        with open(
            "monitoring_devices.csv",
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

        print("Saved monitoring_devices.csv")
        print("Rows:", len(data))

else:
    print(response.text)

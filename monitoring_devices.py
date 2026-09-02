import requests
from requests.auth import HTTPBasicAuth
import csv

url = "https://home.mawingunetworks.com/api/2.0/admin/networking/monitoring"

key = "9687bab6a5e7a924de376513a691f25e"
secret = "dfdec1ee621ccf0b7e3112f3ae571a27"

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
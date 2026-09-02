import requests
from requests.auth import HTTPBasicAuth
import csv

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "API Key"
SECRET = "Secret API"

# Load monitoring devices
response = requests.get(
    f"{BASE_URL}/admin/networking/monitoring",
    auth=HTTPBasicAuth(KEY, SECRET)
)

monitoring = response.json()

switch_lookup = {}

for d in monitoring:

    if d.get("title", "").endswith("_SW"):

        switch_lookup[d["title"]] = d

print("Switches loaded:", len(switch_lookup))


# Build router_id → switch_title map
router_switch = {}

with open(
    "router_contentions.csv",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        if "_SW" in row["title"]:

            router_switch[
                row["router_id"]
            ] = row["title"]


with open(
    "missing_monitoring.csv",
    encoding="utf-8"
) as file:

    rows = csv.DictReader(file)

    for row in rows:

        title = row["title"]

        router_id = row["router_id"]

        switch_name = router_switch.get(
            router_id
        )

        if not switch_name:

            print(
                "No switch:",
                title
            )

            continue

        if switch_name not in switch_lookup:

            print(
                "Switch missing:",
                switch_name
            )

            continue

        switch = switch_lookup[
            switch_name
        ]

        payload = {

            "title": title,

            "network_site_id":
            switch["network_site_id"],

            "parent_id":
            switch["id"],

            "producer": 1,

            "ip": "10.0.0.1",

            "snmp_port": 161,

            "snmp_community": "public",

            "snmp_version": 2,

            "type": 2,

            "monitoring_group": 1,

            "location_id":
            switch["location_id"],

            "is_ping": 1,

            "active": 0,

            "access_device": 1
        }

        r = requests.post(
            f"{BASE_URL}/admin/networking/monitoring",
            auth=HTTPBasicAuth(
                KEY,
                SECRET
            ),
            json=payload
        )

        print(
            title,
            "→",
            switch_name,
            "→",
            r.status_code
        )

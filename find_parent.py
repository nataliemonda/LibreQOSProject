import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "9687bab6a5e7a924de376513a691f25e"
SECRET = "c020d5c275b9218c8fdba9ebc1e81f96"

response = requests.get(
    f"{BASE_URL}/admin/networking/monitoring",
    auth=HTTPBasicAuth(KEY, SECRET)
)

devices = response.json()

target = "MAS"

for d in devices:

    title = d.get("title", "")

    if target in title:

        print(
            "id:", d["id"],
            "| title:", title,
            "| parent:", d["parent_id"]
        )
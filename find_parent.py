import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "API Key"
SECRET = "Secret API"

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

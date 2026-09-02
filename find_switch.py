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

for d in devices:

    title = d.get("title", "")

    if (
        title.endswith("_SW")
        or "MIG" in title
        or "MAS" in title
    ):

        print(
            d["id"],
            "|",
            title,
            "| parent:",
            d["parent_id"]
        )

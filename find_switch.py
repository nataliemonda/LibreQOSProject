import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "9687bab6a5e7a924de376513a691f25e"
SECRET = "12ba30e1fedbb586413cfc2cf5dd93ae"

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
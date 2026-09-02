import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "6b16484d021797bb5be96ffa58ff1a43"
SECRET = "9b29bfc68ebc9729befa0fff5b0e4d32"

search = input("Search: ").upper()

response = requests.get(
    f"{BASE_URL}/admin/networking/monitoring",
    auth=HTTPBasicAuth(KEY, SECRET)
)

devices = response.json()

found = False

for device in devices:

    title = device.get("title", "").upper()

    if search in title:

        found = True

        print("--------------------------------")
        print("ID:", device.get("id"))
        print("TITLE:", device.get("title"))
        print("NETWORK SITE:", device.get("network_site_id"))
        print("LOCATION:", device.get("location_id"))
        print("PARENT:", device.get("parent_id"))

if not found:
    print("Nothing found.")
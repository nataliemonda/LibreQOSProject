import requests
from requests.auth import HTTPBasicAuth
import json

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "6b16484d021797bb5be96ffa58ff1a43"
SECRET = "ac0ecba1f5f1b09c6ac9789705768299"

ROUTER_ID = 18   # MAC_MANZ_BRASS_IPOE

response = requests.get(
    f"{BASE_URL}/admin/networking/monitoring/{ROUTER_ID}",
    auth=HTTPBasicAuth(KEY, SECRET)
)

print("Status:", response.status_code)

print(
    json.dumps(
        response.json(),
        indent=4
    )
)
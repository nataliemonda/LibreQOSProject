import requests
from requests.auth import HTTPBasicAuth
import json

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "API Key"
SECRET = "Secret API"

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

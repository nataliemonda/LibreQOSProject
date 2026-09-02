import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://home.mawingunetworks.com/api/2.0/admin/networking/monitoring/681"

key = "API Key"
secret = "Secret API"

response = requests.get(
    url,
    auth=HTTPBasicAuth(key, secret)
)

print("Status:", response.status_code)

print(
    json.dumps(
        response.json(),
        indent=2
    )
)

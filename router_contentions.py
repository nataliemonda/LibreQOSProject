import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://home.mawingunetworks.com/api/2.0/admin/networking/monitoring/681"

key = "6b16484d021797bb5be96ffa58ff1a43"
secret = "e81d934c83ed576f9c2414b923793289"

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
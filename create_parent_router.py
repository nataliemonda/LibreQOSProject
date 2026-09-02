import requests
from requests.auth import HTTPBasicAuth
import json

BASE_URL = "https://home.mawingunetworks.com/api/2.0"

KEY = "6b16484d021797bb5be96ffa58ff1a43"
SECRET = "0b5bd6d8ae83ac5b9ce7316aef12dd0a"

payload = {
    "title": "ABDS_BRASS_IPOE",
    "parent_id": 0,
    "producer": 1,
    "model": "",
    "ip": "10.255.255.250",
    "snmp_port": 161,
    "snmp_community": "public",
    "snmp_version": 2,
    "type": 1,
    "monitoring_group": 1,
    "is_ping": 1,
    "active": 0,
    "access_device": 0
}

response = requests.post(
    f"{BASE_URL}/admin/networking/monitoring",
    auth=HTTPBasicAuth(KEY, SECRET),
    json=payload
)

print("Status:", response.status_code)

try:
    print(json.dumps(response.json(), indent=4))
except Exception:
    print(response.text)
#   Splynx API v2.0 demo script
#   Author: Roman Muzichuk (Splynx s.r.o.)
#   https://splynx.docs.apiary.io - API documentation

import requests
import time
from datetime import datetime
import os
import hmac
import hashlib
import urllib3

file_paths = [
    './path/file1.txt',
    './path/file2.png',
]
domain_name = "YOUR_SPLYNX_DOMAIN"
api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'
message_id = 'TICKET_MESSAGE_ID'

t_now = datetime.now()
nonce = round((time.mktime(t_now.timetuple()) + t_now.microsecond / 1000000.0) * 100)
st = "%s%s" % (nonce, api_key)
signature = hmac.new(bytes(api_secret.encode('latin-1')), bytes(st.encode('latin-1')), hashlib.sha256).hexdigest()

auth_data = {
    'key': api_key,
    'signature': signature.upper(),
    'nonce': nonce,

}
auth_string = urllib3.request.urlencode(auth_data)
headers = {
    "Authorization": "Splynx-EA (" + auth_string + ")",
}

url = f"{domain_name}/api/2.0/admin/support/ticket-attachments?message_id={message_id}"

files = {}
for index, file_path in enumerate(file_paths):
    file_name = os.path.basename(file_path)
    files['files['+str(index)+']'] = open(file_path, 'rb')

response = requests.request('post', url, files=files, headers=headers)

print(response.text)
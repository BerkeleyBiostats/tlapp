import os
import sys
import requests

token = os.getenv('TLAPP_TOKEN')
if token is None:
    sys.exit("Expecting TLAPP_TOKEN")

logs_url = os.getenv('TLAPP_LOGS_URL')
if logs_url is None:
    sys.exit("Expecting TLAPP_LOGS_URL")

for line in sys.stdin:
    requests.post(logs_url, headers={
        'Authorization': token
    }, data=line)

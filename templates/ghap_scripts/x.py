# "x.py" as in "execute"
import os
import sys
import subprocess
import requests

token = os.getenv('TLAPP_TOKEN')
if token is None:
    sys.exit("Expecting TLAPP_TOKEN")

logs_url = os.getenv('TLAPP_LOGS_URL')
if logs_url is None:
    sys.exit("Expecting TLAPP_LOGS_URL")

process = subprocess.Popen(['sh', 'wrapper.sh'], stdout=subprocess.PIPE)
for line in iter(process.stdout.readline, ''):
	requests.post(logs_url, headers={
        'Authorization': token
    }, data=line)
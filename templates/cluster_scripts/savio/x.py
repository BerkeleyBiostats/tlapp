# "x.py" as in "execute"
import os
import sys
import subprocess
import requests
from datetime import datetime, timedelta

token = os.getenv("TLAPP_TOKEN")
if token is None:
    sys.exit("Expecting TLAPP_TOKEN")

logs_url = os.getenv("TLAPP_LOGS_URL")
if logs_url is None:
    sys.exit("Expecting TLAPP_LOGS_URL")

process = subprocess.Popen(["sh", "wrapper.sh"], stdout=subprocess.PIPE)

last_post = datetime.utcnow()
five_seconds = timedelta(seconds=5)
log_lines = b""

for line in iter(process.stdout.readline, ""):

    log_lines += line

    if datetime.utcnow() - last_post > five_seconds:
        last_post = datetime.utcnow()
        requests.post(logs_url, headers={"Authorization": token}, data=log_lines)
        log_lines = b""

requests.post(logs_url, headers={"Authorization": token}, data=log_lines)

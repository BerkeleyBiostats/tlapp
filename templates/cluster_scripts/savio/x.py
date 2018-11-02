# "x.py" as in "execute"
import os
import sys
import subprocess
import requests
from datetime import datetime, timedelta

token = "{{ token }}"
logs_url = "{{ logs_url }}"

process = subprocess.Popen(["sh", "wrapper.sh"], stdout=subprocess.PIPE)

last_post = datetime.utcnow()
five_seconds = timedelta(seconds=5)
log_lines = b""

for line in iter(process.stdout.readline, b""):

    log_lines += line

    if datetime.utcnow() - last_post > five_seconds:
        last_post = datetime.utcnow()
        requests.post(logs_url, headers={"Authorization": token}, data=log_lines)
        log_lines = b""

requests.post(logs_url, headers={"Authorization": token}, data=log_lines)

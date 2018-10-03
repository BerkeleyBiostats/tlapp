FROM python:3.7.0

RUN apt-get update && apt-get install -yqq xmlsec1
RUN pip install --upgrade pip

# Install dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt
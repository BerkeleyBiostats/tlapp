import os
import json
import requests

job_data = {
    "inputs": {
        "data": {
          "uri": "https://raw.githubusercontent.com/BerkeleyBiostats/tlapp/30821fe37d9fdb2cb645ad2c42f63f1c1644d7c4/cpp.csv",
          "type": "web"
        },
        "nodes": {
          "A": [
            "foo",
            "bar"
          ],
          "W": "baz"
        },
        "script_params": {
          "threshold": True,
          "sample_size": 200
        }
      },
    "backend": "bluevelvet",
    "r_packages": [
        "knitr",
        "github://jeremyrcoyle/delayed@reduce-r-version",
        "igraph@1.0.1"
    ],
    "code": """
---
title: "Sample Longbow Template"
author: "Jeremy Coyle"
date: "9/1/2017"
output: html_document
required_packages:  ['knitr', 'github://jeremyrcoyle/delayed@reduce-r-version', 'igraph@1.0.1']
params:
  data: 
    value: 
      type: 'web'
      uri: 'https://raw.githubusercontent.com/BerkeleyBiostats/tlapp/30821fe37d9fdb2cb645ad2c42f63f1c1644d7c4/cpp.csv'
  nodes:
    value:
      A: ['foo', 'bar']
      W: ['baz']
  script_params:
    value:
      sample_size:
        input: 'numeric'
        value: 200
      threshold:
        input: 'checkbox'
        value: TRUE
  output_directory:
    value: ""
---

```{r setup, include=FALSE}
library(knitr)
knitr::opts_chunk$set(echo = TRUE)
```

```{r params}
library(longbowtools)
data <- get_tl_data()
nodes <- get_tl_nodes()
tl_params <- get_tl_params()
print(data)
print(nodes)
print(tl_params)
```

This is math: $y=x^2$
""",
}

# 128.32.59.171

job_data["ghap_credentials"] = {
    "username": os.environ.get("USERNAME"),
    "password": os.environ.get("PASSWORD"),
    "ip": "bluevelvet.biostat.berkeley.edu",
}

token = os.environ.get("TOKEN")

# Construct URL to submit job
endpoint = "https://www.longbowapp.com/submit_job_token/"

response = requests.post(endpoint, data=json.dumps(job_data), headers={
    "Authorization": token
})

print(response.json())


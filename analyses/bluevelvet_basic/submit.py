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


class Command(BaseCommand):
    help = "Test for regressions after a release"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("password")
        parser.add_argument("ip")

    def handle(self, *args, **options):

        job_data["ghap_credentials"] = {
            "username": options["username"],
            "password": options["password"],
            "ip": options["ip"],
        }

        # Construct URL to submit job
        endpoint = os.path.join(settings.HOSTNAME, "submit_job_token/")

        # Get an admin token
        admin = models.User.objects.filter(is_superuser=True).first()
        token = admin.token.token

        response = requests.post(endpoint, data=json.dumps(job_data), headers={
            "Authorization": token
        })

        print(response.json())


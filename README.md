Longbow
===

![Screenshot](screenshot.png?raw=true "Application Screenshot")

The Longbow application makes it easier to run computationally-intensive notebooks on clusters. 

The application includes such features as

* Real-time monitoring of logs
* Batch jobs of parameterized reports
* Automated provisioning of cluster environments

Currently, the application is used for research purposes on Berkeley's Savio cluster as well as the Global Health and Analytics Platform.

Basic Usage
---

The simplest way to interact with Longbow is through RStudio. There is a helper package, `tlverse/longbowtools`, for this.

    devtools::install_github('tlverse/longbowtools')
    library(longbowtools)

You can test scripts locally first:

    run_locally("~/script.Rmd", "~/inputs.json", output_directory="~/output")

Then submit to Longbow to be run on a cluster:
    
    configure_cluster("~/cluster_credentials.json")
    run_on_longbow("~/script.Rmd", "~/inputs.json", output_directory="~/output")

[Details on configuration](https://github.com/tlverse/longbowtools#longbow-templates) can be found in the longbowtools repository.

Also, a number of detailed examples can be found in this repository in the [sample analyses folder](analyses).

***

Web Application Development Environment
---

It is possible to run Longbow locally using Docker.

The development environment expects that you have [direnv](https://github.com/direnv/direnv) installed.

Add a `secrets.env` file with the following contents:

```
export SAVIO_USERNAME=...
export SAVIO_PIN=...
export SAVIO_SECRET=...
export GHAP_USERNAME=...
export GHAP_IP=...
export GHAP_PASSWORD=...
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export PROD_API_TOKEN=...
export NGROK_TOKEN=...
export GITHUB_TOKEN=...
```

Then,

```
docker-compose up
```

A number of helper scripts are included. See the (dev-scripts)[dev-scripts] folder. 

Creative Commons Credits
---

Bow Icon: bow by Milky - Digital innovation from the Noun Project
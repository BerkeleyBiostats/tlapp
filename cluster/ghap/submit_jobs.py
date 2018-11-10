from urllib.parse import urlparse, urlunparse
import boto3
import datetime
from datetime import timedelta
import json
import logging
import os
import pipes
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback
import uuid
from fabric.connection import Connection
from django.conf import settings
from django.core.cache import cache
from django.template import loader, Context
from core import models
from ..redirect_logs import redirect_logs
from ..generate_s3_urls import generate_s3_urls
from ..file_creator import FileCreator

logger = logging.getLogger("django")


file_creator = FileCreator()


def make_temp_dir_name():
    return str(uuid.uuid4())


def make_temp_dir(base_dir):
    return os.path.join(base_dir, make_temp_dir_name())


def ensure_dataset(job, username, password):

    # Check if we need to clone a dataset
    ghap_dataset_url = None
    if (
        "data" in job.inputs
        and "uri" in job.inputs["data"]
        and "repository_path" in job.inputs["data"]
    ):
        ghap_dataset_url = job.inputs["data"]["uri"]
        ghap_repo_path = job.inputs["data"]["repository_path"]
    else:
        return

    # For job restarting, the job.inputs.data.uri will have
    # changed. The old value is stored in
    # job.inputs.data.ghap_dataset_url
    if "data" in job.inputs and "ghap_dataset_url" in job.inputs["data"]:
        ghap_dataset_url = job.inputs["data"]["ghap_dataset_url"]

    o = urlparse(ghap_dataset_url)
    repo_name = o.path.split("/")[-1][:-4]
    repo_base_path = "~/datasets"
    repo_path = os.path.join(repo_base_path, repo_name)

    # Set the uri to the file's path on the local file system
    # (used by tltools)
    job.inputs["data"]["uri"] = os.path.join(repo_path, ghap_repo_path)
    job.inputs["data"]["ghap_dataset_url"] = ghap_dataset_url

    # Add username and password to the git url
    o = list(tuple(o))
    o[1] = username + ":" + pipes.quote(password) + "@" + o[1]
    git_url_with_password = urlunparse(tuple(o))

    file_creator.create_file(
        name="ensure_git_dataset.sh",
        template="cluster_scripts/ghap/ensure_git_dataset",
        template_context={
            "repo_base_path": repo_base_path,
            "repo_path": repo_path,
            "git_url_with_password": git_url_with_password
        },
        executable=True
    )

def upload_to_ghap(c, job, username, password):
    temp_base_dir = "/tmp"
    remote_code_folder_name = make_temp_dir_name()
    remote_code_folder = os.path.join(temp_base_dir, remote_code_folder_name)
    remote_output_folder = make_temp_dir_name()
    remote_output_folder_full_path = os.path.join(remote_code_folder, remote_output_folder)
    local_code_folder = tempfile.mkdtemp()

    file_creator.initialize(local_code_folder)

    ensure_dataset(job, username, password)

    file_creator.create_file(
        name="script.Rmd",
        content=job.code
    )

    file_creator.create_file(
        name="runner.R",
        template="cluster_scripts/runner.R",
        executable=True
    )

    file_creator.create_file(
        name="inputs.json",
        content=json.dumps(job.inputs)
    )

    file_creator.create_file(
        name="provision.sh",
        content=job.provision,
        executable=True
    )

    s3_urls = generate_s3_urls(remote_output_folder)
    output_put_url = s3_urls["put"]
    job.output_url = s3_urls["get"]
    job.save(update_fields=["output_url"])

    cmd = "Rscript --default-packages=methods,stats,utils %s %s %s %s" % (
        remote_runner_script_filename,
        remote_code_filename,
        remote_input_filename,
        remote_output_folder_full_path,
    )

    logger.info("Command to run:")
    logger.info(cmd)

    # upload x.py
    base_url = None
    if job.base_url:
        base_url = job.base_url
    else:
        base_url = os.environ.get("BASE_URL")

    # TODO: generate the url using django url and join with urllib
    token = job.created_by.token.token
    logs_url = base_url + "jobs/%s/append_log/" % job.id
    heartbeat_url = base_url + "jobs/%s/heartbeat/" % job.id

    file_creator.create_file(
        name="x.py",
        template="cluster_scripts/x.py",
        template_params={
            "token": token,
            "logs_url": logs_url,
            "heartbeat_url": heartbeat_url,
        },
        executable=True
    )

    file_creator.create_file(
        name="wrapper.sh",
        template="cluster_scripts/savio/wrapper.sh",
        template_params={
            "github_token": settings.GITHUB_TOKEN,
            "token": token,
            "logs_url": logs_url,
            "job_url": job_url,
            "finish_url": base_url + "jobs/%s/finish/" % job.id,
            "r_cmd": cmd,
            "tar_file": remote_output_folder + ".tar.gz",
            "output_dir": remote_output_folder,
            "put_url": output_put_url,
        }
    )

    file_creator.create_directory(name=remote_output_folder)

    # TODO: upload all the scripts

    # Tar and upload it
    local_bundle_folder = local_code_folder
    tar_basename = os.path.basename(local_bundle_folder)
    tar_filename = tar_basename + ".tar.gz"
    tar_fullpath = local_bundle_folder + ".tar.gz"
    with tarfile.open(tar_fullpath, "w:gz") as tar:
        tar.add(local_bundle_folder, arcname=os.path.basename(local_bundle_folder))
    c.put(tar_fullpath, remote=temp_base_dir)

    # Fire up the job in screen
    commands = [
        "cd %s" % temp_base_dir,
        "tar xvzf %s --strip 1" % tar_filename,
        "cd %s" % remote_code_folder,
        "pip install requests --user",
        "export TLAPP_TOKEN=%s" % token,
        "export TLAPP_LOGS_URL=%s" % logs_url,
        "screen -d -m python x.py",
        "sleep 1",
    ]
    command = ";".join(commands)
    logger.info(command)
    output = c.run(command)

    return output


def run_ghap_job(job):
    username = job.ghap_username
    server = job.ghap_ip
    password = cache.get("ghap_password_%s" % job.id)
    host = "%s@%s" % (username, server)
    with Connection(host=host, connect_kwargs={"password": password}) as c:
        output = upload_to_ghap(c, job, username, password)


def submit_job(job):
    job.status = models.ModelRun.status_choices["running"]
    job.last_heartbeat = datetime.datetime.utcnow()
    job.save(update_fields=["status", "last_heartbeat"])
    with redirect_logs(job):
        run_ghap_job(job)
    job.save()


def submit_jobs(jobs):
    for job in jobs:
        submit_job(job)

from contextlib import redirect_stdout, redirect_stderr
import boto3
import datetime
import io
import json
import logging
import os
import sys
import tarfile
import tempfile
import traceback
import uuid
from fabric.connection import Connection
from django.template import loader, Context
from django.conf import settings
from core import models
from ..redirect_logs import redirect_logs

logger = logging.getLogger('django')

def make_temp_dir_name():
    return str(uuid.uuid4())


def make_temp_dir(base_dir):
    return os.path.join(base_dir, make_temp_dir_name())


def generate_s3_urls(remote_output_folder):
    s3 = boto3.client("s3")
    bucket = "tlapp"
    zipped_outputs_filename = remote_output_folder + ".tar.gz"
    key = zipped_outputs_filename
    put_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=60 * 60 * 24 * 30,
        HttpMethod="PUT",
    )
    get_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=60 * 60 * 24 * 30
    )

    return {
        "get": get_url,
        "put": put_url
    }


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_job_files(bundle_folder, job):
    local_code_folder = make_temp_dir_name()
    local_code_folder_full_path = os.path.join(bundle_folder, local_code_folder)
    ensure_dir(local_code_folder_full_path)

    remote_output_folder = make_temp_dir_name()
    remote_output_folder_full_path = "~/longbow/%s/%s" % (local_code_folder, remote_output_folder)

    def create_file(name=None, content=None, copy_from_path=None, template=None, template_params=None, executable=False):
        if copy_from_path:
            with open(copy_from_path) as f:
                content = f.read()
        if template:
            template = loader.get_template(template)
            content = template.render(template_params)
        filename = os.path.join(local_code_folder_full_path, name)
        with open(filename, "w") as f:
            f.write(content)
        if executable:
            os.chmod(filename, 0o755)

    def create_directory(name=None):
        path = os.path.join(local_code_folder_full_path, name)
        os.mkdir(path)

    create_file(
        name="script.Rmd",
        content=job.code,
        executable=True
    )

    create_file(
        name="runner.R",
        template="cluster_scripts/runner.R",
        executable=True
    )
    
    create_file(
        name="inputs.json",
        content=json.dumps(job.inputs)
    )

    create_file(
        name="provision.sh",
        content=job.provision,
        executable=True
    )

    create_file(
        name="slurm.sh",
        template="cluster_scripts/savio/slurm.sh",
        template_params={
            "id": job.id
        },
        executable=True
    )

    create_directory(name=remote_output_folder)

    # Generate signed PUT url for outputs zip
    s3_urls = generate_s3_urls(remote_output_folder)
    output_put_url = s3_urls["put"]
    job.output_url = s3_urls["get"]
    job.save(update_fields=["output_url"])

    cmd = "Rscript --default-packages=methods,stats,utils %s %s %s %s" % (
        "runner.R",
        "script.Rmd",
        "inputs.json",
        remote_output_folder_full_path,
    )

    # Generate wrapper script
    wrapper_script_template = loader.get_template("cluster_scripts/savio/wrapper.sh")

    token = job.created_by.token.token

    if job.base_url:
        base_url = job.base_url
    else:
        base_url = os.environ.get("BASE_URL")

    # TODO: generate the url using django url and join with urllib
    logs_url = base_url + "jobs/%s/append_log/" % job.id
    heartbeat_url = base_url + "jobs/%s/heartbeat/" % job.id
    job_url = base_url + "jobs/%s/" % job.id

    create_file(
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

    create_file(
        name="x.py",
        template="cluster_scripts/x.py",
        template_params={
            "token": token,
            "logs_url": logs_url,
            "heartbeat_url": heartbeat_url,
        },
        executable=True
    )

    return local_code_folder    


def submit_savio_jobs(jobs, username, password, parent=None):

    local_bundle_folder = tempfile.mkdtemp()

    job_dir_names = []

    if parent:
        job_dir_names.append(create_job_files(local_bundle_folder, parent))

    for job in jobs:
        job_dir_names.append(create_job_files(local_bundle_folder, job))

    # Tar it
    with tarfile.open(local_bundle_folder + ".tar.gz", "w:gz") as tar:
        tar.add(local_bundle_folder, arcname=os.path.basename(local_bundle_folder))

    # Upload to S3
    tar_basename = os.path.basename(local_bundle_folder)
    tar_filename = tar_basename + ".tar.gz"
    tar_fullpath = local_bundle_folder + ".tar.gz"
    s3_key = "jobs/%s" % tar_filename    
    s3 = boto3.resource("s3")
    s3.Object("tlapp", s3_key).upload_file(tar_fullpath)

    # Generate GET URL
    s3 = boto3.client("s3")
    get_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": "tlapp", "Key": s3_key}, ExpiresIn=60 * 60 * 24 * 30
    )

    # Create string of commands to download, untar, and run
    commands = [
        "mkdir -p ~/longbow",
        "cd ~/longbow",
        "module load python",
        "module load r",
        "pip install requests --user",
        "wget -O %s '%s'" % (tar_filename, get_url),
        "tar xvzf %s --strip 1" % tar_filename,
    ]

    # TODO: if there's a parent job, add the dependency flag
    created_parent_job = False

    for job_dir_name in job_dir_names:
        commands.append("cd %s" % job_dir_name)

        if parent and not created_parent_job:
            commands.append("parentjobid=$(sbatch slurm.sh | cut -d' ' -f4)")
            created_parent_job = True
        elif parent:
            commands.append("sbatch --dependency=afterok:$parentjobid slurm.sh")
        else:
            commands.append("sbatch slurm.sh")

        commands.append("cd ..")

    command = ";".join(commands)

    # .run them
    server = "hpc.brc.berkeley.edu"
    host = "%s@%s" % (username, server)
    with Connection(host=host, connect_kwargs={"password": password}) as c:
        output = c.run(command)

    return output


def submit_jobs(jobs, username, password):

    parent = None

    if isinstance(jobs, dict):
        parent = jobs["parent"]
        jobs = jobs["children"]

    for job in jobs:
        job.status = models.ModelRun.status_choices["submitted"]
        job.save(update_fields=["status"])

    with redirect_logs(job):
        submit_savio_jobs(jobs, username, password, parent=parent)




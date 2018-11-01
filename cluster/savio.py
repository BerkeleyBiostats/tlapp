from contextlib import redirect_stdout, redirect_stderr
import boto3
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
from core import models

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


def submit_savio_job(job, username, password):

    # Create the job bundle
    local_code_folder = tempfile.mkdtemp()

    remote_output_folder = make_temp_dir_name()
    remote_output_folder_full_path = "~/longbow/%s/%s" % (os.path.basename(local_code_folder), remote_output_folder)

    def create_file(name=None, content=None, copy_from_path=None, template=None, template_params=None, executable=False):
        if copy_from_path:
            with open(copy_from_path) as f:
                content = f.read()
        if template:
            template = loader.get_template(template)
            content = template.render(template_params)
        filename = os.path.join(local_code_folder, name)
        with open(filename, "w") as f:
            f.write(content)
        if executable:
            os.chmod(filename, 0o755)

    create_file(
        name="script.Rmd",
        content=job.code,
        executable=True
    )

    create_file(
        name="runner.R",
        copy_from_path=os.path.join(os.environ.get("APP_ROOT"), "runner.R"),
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
        name="x.py",
        template="cluster_scripts/savio/x.py",
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
    job_url = base_url + "jobs/%s/" % job.id

    create_file(
        name="wrapper.sh",
        template="cluster_scripts/savio/wrapper.sh",
        template_params={
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

    # Tar it
    with tarfile.open(local_code_folder + ".tar.gz", "w:gz") as tar:
        tar.add(local_code_folder, arcname=os.path.basename(local_code_folder))

    # Upload to S3
    tar_basename = os.path.basename(local_code_folder)
    tar_filename = tar_basename + ".tar.gz"
    tar_fullpath = local_code_folder + ".tar.gz"
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
        "mkdir -p %s" % remote_output_folder_full_path,
        "cd ~/longbow",
        "wget -O %s '%s'" % (tar_filename, get_url),
        "tar xvzf %s" % tar_filename,
        "cd %s" % tar_basename,
        "module load python",
        "module load r",
        "pip install requests --user",
        "export TLAPP_TOKEN=%s" % token,
        "export TLAPP_LOGS_URL=%s" % logs_url,
        "sbatch slurm.sh"
    ]

    command = ";".join(commands)

    # .run them
    server = "hpc.brc.berkeley.edu"
    host = "%s@%s" % (username, server)
    with Connection(host=host, connect_kwargs={"password": password}) as c:
        output = c.run(command)

    return output

class StreamingStringIO(io.StringIO):
    def __init__(self, job):
        self.job = job
        io.StringIO.__init__(self)

    def write(self, s):
        io.StringIO.write(self, s)
        self.job.output = self.getvalue()
        self.job.save(update_fields=["output"])

def submit_job(job, username, password):
    job.status = models.ModelRun.status_choices["submitted"]
    job.save(update_fields=["status"])

    f = StreamingStringIO(job)
    with redirect_stdout(f), redirect_stderr(f):
        try:
            submit_savio_job(job, username, password)
        except:
            traceback.print_exc()
            job.status = models.ModelRun.status_choices["error"]
            job.save(update_fields=["status"])


from contextlib import redirect_stdout, redirect_stderr
from urllib.parse import urlparse, urlunparse
import boto3
import datetime
from datetime import timedelta
import io
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
from django.db.models import Q
from django.core.cache import cache
from django.template import loader, Context
from bs4 import BeautifulSoup
from core import models

logger = logging.getLogger('django')


def put_script(c, content=None, script_name=None, local_code_folder=None, remote_code_folder=None):
    # write locally
    local_code_filename = os.path.join(local_code_folder, script_name)
    with open(local_code_filename, 'w') as code_file:
        code_file.write(content)
    # push to cluster
    remote_code_filename = os.path.join(remote_code_folder, script_name)
    os.chmod(local_code_filename, 0o755)
    c.put(local_code_filename, remote_code_filename)
    logger.info("Put code at %s" % remote_code_filename)


def pwd():
    output = run('pwd')
    return output

def make_temp_dir_name():
    return str(uuid.uuid4())

def make_temp_dir(base_dir):
    return os.path.join(base_dir, make_temp_dir_name())


def upload_to_ghap(c, job, username, password):
    temp_base_dir = '/tmp'
    remote_output_folder = make_temp_dir_name()
    remote_output_folder_full_path = os.path.join(temp_base_dir, remote_output_folder)
    c.run('mkdir -p %s' % remote_output_folder_full_path)

    # Check if we need to clone a dataset
    ghap_dataset_url = None
    if job.dataset and job.dataset.url.startswith('https://git.ghap.io'):
        ghap_dataset_url = job.dataset.url
        ghap_repo_path = job.dataset.repository_path
    if 'data' in job.inputs and \
       'uri' in job.inputs['data'] and \
       'repository_path' in job.inputs['data']:
        ghap_dataset_url = job.inputs['data']['uri']
        ghap_repo_path = job.inputs['data']['repository_path']

    # For job restarting, the job.inputs.data.uri will have
    # changed. The old value is stored in 
    # job.inputs.data.ghap_dataset_url
    if 'data' in job.inputs and \
        'ghap_dataset_url' in job.inputs['data']:
        ghap_dataset_url = job.inputs['data']['ghap_dataset_url']

    if ghap_dataset_url:

        # Check if the dataset has already been cloned
        o = urlparse(ghap_dataset_url)
        repo_name = o.path.split('/')[-1][:-4]
        repo_base_path = '~/datasets'
        repo_path = os.path.join(repo_base_path, repo_name)
        repo_exists = c.exists(repo_path)

        # Set the uri to the file's path on the local file system
        # (used by tltools)
        job.inputs['data']['uri'] = os.path.join(repo_path, ghap_repo_path)
        job.inputs['data']['ghap_dataset_url'] = ghap_dataset_url

        if repo_exists:
            logger.info("Not going to clone git repo since it already exists")
        else:
            # Add username and password to the git url
            o = list(tuple(o))
            o[1] = username + ":" + pipes.quote(password) + "@" + o[1]
            git_url_with_password = urlunparse(tuple(o))

            # Clone it, hiding the command so password doesn't appear in logs
            with c.cd(repo_base_path), c.hide('running'):
                c.run('git clone %s' % git_url_with_password)

    # Write script to a file...    
    local_code_folder = tempfile.mkdtemp()
    script_name = 'script.Rmd'
    local_code_filename = os.path.join(local_code_folder, script_name)
    with open(local_code_filename, 'w') as code_file:
        if job.code:
            code_file.write(job.code)
        else:
            code_file.write(job.model_template.code)
    # ...then upload to cluster
    remote_code_folder = make_temp_dir(temp_base_dir)
    remote_code_filename = os.path.join(remote_code_folder, script_name)
    c.run('mkdir -p %s' % remote_code_folder)
    c.put(local_code_filename, remote_code_filename)
    logger.info("Put code at %s" % remote_code_filename)

    # Write runner script to a file...
    app_root = os.environ.get("APP_ROOT")
    runner_script_filename = os.path.join(app_root, "runner.R")
    remote_runner_script_filename = os.path.join(remote_code_folder, 'runner.R')
    c.put(runner_script_filename, remote_runner_script_filename)

    # Write inputs to a file...
    input_name = 'inputs.json'
    local_input_filename = os.path.join(local_code_folder, input_name)  

    if not job.inputs:
        inputs = {}
    elif 'params' in job.inputs:
        inputs = job.inputs['params']
    else:
        inputs = job.inputs

    with open(local_input_filename, 'w') as input_file:
        input_file.write(json.dumps(inputs))
    remote_input_filename = os.path.join(remote_code_folder, input_name)
    # ...then upload to cluster
    c.put(local_input_filename, remote_input_filename)
    logger.info("Put inputs at %s" % remote_input_filename)

    # Upload and run a provisioning script
    provision_code = None
    if job.model_template and job.model_template.provision:
        provision_code = job.model_template.provision
    elif job.provision:
        provision_code = job.provision

    if provision_code:
        provision_name = 'provision.sh'
        local_provision_filename = os.path.join(local_code_folder, provision_name)
        with open(local_provision_filename, 'w') as provision_file:
            provision_file.write(provision_code)
        remote_provision_filename = os.path.join(remote_code_folder, provision_name)
        os.chmod(local_provision_filename, 0o755)
        c.put(local_provision_filename, remote_provision_filename)
        logger.info("Put provision script at %s" % remote_provision_filename)

        # TODO: make sure provision is run in screen session
        # with cd(remote_code_folder):
        #     cmd = "./provision.sh"
        #     provision_output = run(cmd)

    # Generate signed PUT url for outputs zip
    s3 = boto3.client('s3')
    bucket = 'tlapp'
    zipped_outputs_filename = remote_output_folder + ".tar.gz"
    key = zipped_outputs_filename
    output_put_url = s3.generate_presigned_url(
        'put_object', 
        Params={'Bucket': bucket, 'Key': key}, 
        ExpiresIn=60*60*24*30,
        HttpMethod='PUT')
    logger.info("Output PUT URL")
    logger.info(output_put_url)

    # Save this url for downloading later
    url = s3.generate_presigned_url(
        'get_object', 
        Params={'Bucket': bucket, 'Key': key}, 
        ExpiresIn=60*60*24*30)
    job.output_url = url

    # Now run the script
    remote_output_filename = os.path.join(remote_output_folder_full_path, "REPORT.md")

    # TODO: run this in screen session
    cmd = "Rscript --default-packages=methods,stats,utils %s %s %s %s" % (
        remote_runner_script_filename,
        remote_code_filename,
        remote_input_filename,
        remote_output_folder_full_path
    )

    logger.info("Command to run:")
    logger.info(cmd)

    # upload x.py
    heartbeat_url = base_url + "jobs/%s/heartbeat/" % job.id

    x_template = loader.get_template('ghap_scripts/x.py')
    x_script = x_template.render({
        "heartbeat_url": heartbeat_url,
    })
    put_script(c, 
        content=x_script, 
        script_name='x.py',
        local_code_folder=local_code_folder,
        remote_code_folder=remote_code_folder)

    # Generate wrapper script for screen session
    wrapper_script_template = loader.get_template('ghap_scripts/wrapper.sh')

    # TODO: generate the url using django url and join with urllib
    token = job.created_by.token.token

    if job.base_url: 
        base_url = job.base_url
    else:
        base_url = os.environ.get("BASE_URL")

    logs_url = base_url + "jobs/%s/append_log/" % job.id

    wrapper_script = wrapper_script_template.render({
        "token": token,
        "logs_url": logs_url,
        "finish_url": base_url + "jobs/%s/finish/" % job.id,
        "r_cmd": cmd,
        "tar_file": zipped_outputs_filename,
        "output_dir": remote_output_folder,
        "put_url": output_put_url
    })
    put_script(c, 
        content=wrapper_script,
        script_name='wrapper.sh',
        local_code_folder=local_code_folder,
        remote_code_folder=remote_code_folder
    )

    # Fire up the job in screen
    commands = [
        "cd %s" % remote_code_folder,
        "pip install requests --user",
        "export TLAPP_TOKEN=%s" % token,
        "export TLAPP_LOGS_URL=%s" % logs_url,
        "screen -d -m python x.py",
        "sleep 1"
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

def run_vps_job(job):
    code_folder = tempfile.mkdtemp()
    output_folder = tempfile.mkdtemp()

    logger.info(code_folder)
    logger.info("Outputs %s" % output_folder)

    script_name = 'script.R'
    code_filename = os.path.join(code_folder, script_name)
    logger.info(code_filename)
    with open(code_filename, 'w') as code_file:
        code_file.write(job.model_template.code)

    input_name = 'inputs.json'
    input_filename = os.path.join(code_folder, input_name)
    logger.info(input_name)

    inputs = job.inputs
    inputs['output_directory'] = output_folder

    with open(input_filename, 'w') as input_file:
        input_file.write(json.dumps(job.inputs))

    rpath = '/usr/local/lib/R/site-library/longbowtools/'
    cmd = [
        "Rscript",
        "--default-packages=methods,stats",
        rpath + "scripts/run_job.R",
        code_filename,
        input_filename,
    ]

    logger.info(" ".join(cmd))

    script_resp = subprocess.check_output(cmd)
    job.output = script_resp

    shutil.make_archive(output_folder, "zip", output_folder)
    output_zip_filename = output_folder + ".zip"

    s3 = boto3.client('s3')
    key = os.path.basename(output_zip_filename)
    bucket = 'tlapp'
    s3.upload_file(output_zip_filename, bucket, key)

    url = s3.generate_presigned_url(
        'get_object', 
        Params={'Bucket': bucket, 'Key': key}, ExpiresIn=60*60*24*30)

    job.output_url = url
    logger.info(url)

    report_filename = os.path.join(output_folder, 'REPORT.html')
    with open(report_filename, mode='r') as report_file:
        report_content = report_file.read()
    job.output = report_content

    job.status = models.ModelRun.status_choices['success']

class StreamingStringIO(io.StringIO):
     def __init__(self, job):
         self.job = job
         io.StringIO.__init__(self)

     def write(self,s):
         io.StringIO.write(self, s)
         self.job.output = self.getvalue()
         self.job.save()

def reap_stalled_jobs():
    five_minutes_ago = datetime.datetime.utcnow() - timedelta(minutes=5)
    stalled_jobs = models.ModelRun.objects.filter(
        last_heartbeat__lte=five_minutes_ago,
        status=models.ModelRun.status_choices['running'],
    )
    for job in stalled_jobs.all():
        job.status = models.ModelRun.status_choices['error']
        job.traceback = "Job run stalled (heartbeat check)"
        job.save(update_fields=["status", "traceback"])

def handle_jobs():
    reap_stalled_jobs()

    # Pick off a random ModelRun job
    job = models.ModelRun.objects.filter(
        status=models.ModelRun.status_choices['queued']
    ).order_by('?').first()

    if job is None:
        return 0

    if job.created_by.running_job_count() >= settings.MAX_CONCURRENT_JOBS:
        return 0

    job.status = models.ModelRun.status_choices['running']
    job.last_heartbeat = datetime.datetime.utcnow()
    job.save()

    f = StreamingStringIO(job)

    with redirect_stdout(f), redirect_stderr(f):        
        try:
            if job.backend == 'ghap':
                run_ghap_job(job)
            elif job.backend == 'bluevelvet':
                run_ghap_job(job)

            job.save()
        except: 
            traceback.print_exc()
            job.status = models.ModelRun.status_choices['error']

    job.output = f.getvalue()
    logger.info(job.output)
    job.save()

    return 1
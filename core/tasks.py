from urlparse import urlparse, urlunparse
import pipes
import logging
import tempfile
import os
import uuid
import subprocess
import traceback
import json
import shutil
import boto3
from fabric.api import *
from fabric.operations import *
from fabric.contrib.files import exists
from django.core.cache import cache
from core import models

def pwd():
    output = run('pwd')
    return output

def make_temp_dir_name():
    return str(uuid.uuid4())

def make_temp_dir(base_dir):
    return os.path.join(base_dir, make_temp_dir_name())

def upload_to_ghap(job, username, password):
    temp_base_dir = '/tmp'
    remote_output_folder = make_temp_dir_name()
    remote_output_folder_full_path = os.path.join(temp_base_dir, remote_output_folder)

    # Check if we need to clone a dataset
    if job.dataset.url.startswith('https://git.ghap.io'):

        # Check if the dataset has already been cloned
        o = urlparse(job.dataset.url)
        repo_name = o.path.split('/')[-1][:-4]
        repo_base_path = '~/datasets'
        repo_path = os.path.join(repo_base_path, repo_name)
        repo_exists = exists(repo_path)

        # Set the uri to the file's path on the local file system
        job.inputs['data']['uri'] = os.path.join(repo_path, job.dataset.repository_path)

        if repo_exists:
            print("Not going to clone git repo since it already exists")
        else:

            # Add username and password to the git url
            o = list(tuple(o))
            o[1] = username + ":" + pipes.quote(password) + "@" + o[1]
            git_url_with_password = urlunparse(tuple(o))

            # Clone it
            with cd(repo_base_path):
                run('git clone %s' % git_url_with_password)

        


    # Write script to a file...    
    local_code_folder = tempfile.mkdtemp()
    script_name = 'script.R'
    local_code_filename = os.path.join(local_code_folder, script_name)
    with open(local_code_filename, 'w') as code_file:
        code_file.write(job.model_template.code)
    # ...then upload to cluster
    remote_code_folder = make_temp_dir(temp_base_dir)
    remote_code_filename = os.path.join(remote_code_folder, script_name)
    run('mkdir -p %s' % remote_code_folder)
    put(local_code_filename, remote_code_filename)
    print("Put code at %s" % remote_code_filename)

    # Write inputs to a file...
    input_name = 'inputs.json'
    local_input_filename = os.path.join(local_code_folder, input_name)
    inputs = job.inputs
    inputs['output_directory'] = remote_output_folder_full_path
    with open(local_input_filename, 'w') as input_file:
        input_file.write(json.dumps(job.inputs))
    remote_input_filename = os.path.join(remote_code_folder, input_name)
    # ...then upload to cluster
    put(local_input_filename, remote_input_filename)
    print("Put inputs at %s" % remote_input_filename)

    # Upload and run a provisioning script
    if job.model_template.provision:
        provision_name = 'provision.sh'
        local_provision_filename = os.path.join(local_code_folder, provision_name)
        with open(local_provision_filename, 'w') as provision_file:
            provision_file.write(job.model_template.provision)
        remote_provision_filename = os.path.join(remote_code_folder, provision_name)
        put(local_provision_filename, remote_provision_filename, mode=0755)
        print("Put provision script at %s" % remote_provision_filename)

        with cd(remote_code_folder):
            cmd = "./provision.sh"
            provision_output = run(cmd)

    # Now run the script
    run_job_path = '/data/R/x86_64-redhat-linux-gnu-library/3.2/tltools/scripts/run_job.R'

    cmd = "Rscript --default-packages=methods,stats,utils %s %s %s" % (
        run_job_path,
        remote_code_filename,
        remote_input_filename
    )
    output = run(cmd)
    job.output = output

    # Zip up the outputs
    with cd('/tmp'):
        zipped_outputs_filename = remote_output_folder + ".tar.gz"
        run('tar -zcvf %s %s' % (zipped_outputs_filename, remote_output_folder))
        local_outputs_filename = get(zipped_outputs_filename)[0]

    print("Downloaded outputs to %s" % local_outputs_filename)

    s3 = boto3.client('s3')
    key = zipped_outputs_filename
    bucket = 'tlapp'
    s3.upload_file(local_outputs_filename, bucket, key)

    print("Uploaded outputs to %s" % key)

    url = s3.generate_presigned_url(
        'get_object', 
        Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)

    job.output_url = url
    print("Signed url for outputs %s" % url)

    return output

def run_ghap_job(job):
    # Configure login parameters for fabric ssh connection
    username = job.ghap_username
    server = job.ghap_ip
    password = cache.get("ghap_password_%s" % job.id)
    env.hosts = ["%s@%s" % (username, server)]
    env.passwords = {
        "%s@%s:22" % (username, server): password
    }

    output = execute(upload_to_ghap, job, username, password)

    job.output = output
    job.status = models.ModelRun.status_choices['success']

def run_vps_job(job):
    code_folder = tempfile.mkdtemp()
    output_folder = tempfile.mkdtemp()

    print(code_folder)
    print("Outputs %s" % output_folder)

    script_name = 'script.R'
    code_filename = os.path.join(code_folder, script_name)
    print(code_filename)
    with open(code_filename, 'w') as code_file:
        code_file.write(job.model_template.code)

    input_name = 'inputs.json'
    input_filename = os.path.join(code_folder, input_name)
    print(input_name)

    inputs = job.inputs
    inputs['output_directory'] = output_folder

    with open(input_filename, 'w') as input_file:
        input_file.write(json.dumps(job.inputs))

    rpath = '/usr/local/lib/R/site-library/tltools/'
    cmd = [
        "Rscript",
        "--default-packages=methods,stats",
        rpath + "scripts/run_job.R",
        code_filename,
        input_filename,
    ]

    print(" ".join(cmd))

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
        Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)

    job.output_url = url
    print(url)

    report_filename = os.path.join(output_folder, 'REPORT.html')
    with open(report_filename, mode='r') as report_file:
        report_content = report_file.read()
    job.output = report_content

    job.status = models.ModelRun.status_choices['success']

def handle_jobs():
    # Pick off a random ModelRun job
    job = models.ModelRun.objects.filter(
        status=models.ModelRun.status_choices['submitted'],
    ).first()

    if job is None:
        return 0

    job.status = models.ModelRun.status_choices['running']
    job.save()

    try:
        if job.backend == 'ghap':
            run_ghap_job(job)
        else:
            # TODO: this won't work running it on Heroku. 
            # Maybe reimplement as ssh flow like ghap job?
            # run_vps_job(job)
            pass
    except: 
        print(traceback.format_exc())
        job.traceback = traceback.format_exc()
        job.status = models.ModelRun.status_choices['error']

    job.save()

    return 1
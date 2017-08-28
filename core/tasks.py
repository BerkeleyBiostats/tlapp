import logging
import tempfile
import os
import subprocess
from core import models

def handle_jobs():
    # Pick off a random ModelRun job
    job = models.ModelRun.objects.filter(
        status=models.ModelRun.status_choices['submitted'],
    ).first()

    if job is None:
        return 0

    job.status = models.ModelRun.status_choices['running']
    job.save()

    code_folder = tempfile.mkdtemp()
    code_filename = os.path.join(code_folder, 'script.R')
    with open(code_filename, 'w') as code_file:
        code_file.write(job.model_template.code)
    
    script_resp = subprocess.check_output([
        "Rscript",
        code_filename],
        cwd=code_folder)

    print("Ran the job:")
    print(script_resp)

    job.status = models.ModelRun.status_choices['success']
    job.save()

    return 1
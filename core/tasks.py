import logging
import tempfile
import os
import subprocess
import traceback
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

    try:
        code_folder = tempfile.mkdtemp()

        print(code_folder)

        script_name = 'script.R'
        code_filename = os.path.join(code_folder, script_name)
        print(code_filename)
        with open(code_filename, 'w') as code_file:
            code_file.write(job.model_template.code)
        
        script_resp = subprocess.check_output(["Rscript", "--default-packages=methods,stats", code_filename])

        job.output = script_resp
        job.status = models.ModelRun.status_choices['success']
    except:
        print(traceback.format_exc())
        job.traceback = traceback.format_exc()
        job.status = models.ModelRun.status_choices['error']

    job.save()

    return 1
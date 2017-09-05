import logging
import tempfile
import os
import subprocess
import traceback
import json
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

        parameters = job.model_template.parameters
        parameters['output_directory'] = output_folder

        with open(input_filename, 'w') as input_file:
            input_file.write(json.dumps(job.model_template.parameters))
        
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
        job.status = models.ModelRun.status_choices['success']
    except:
        print(traceback.format_exc())
        job.traceback = traceback.format_exc()
        job.status = models.ModelRun.status_choices['error']

    job.save()

    return 1
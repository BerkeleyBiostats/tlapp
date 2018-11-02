from cluster.parse_notebook import get_yaml_header
from cluster.provision_code_generator import build_provision_code
from core import models

def create_jobs(created_by, job_data):

    inputs = job_data.get("inputs", {})

    # Create multiple jobs if `job_data["inputs"]` is a list
    if isinstance(inputs, list):
        job_list = []
        for inputs_dict in inputs:
            single_job_data = job_data.copy()
            single_job_data["inputs"] = inputs_dict
            job_list.extend(create_jobs(created_by, single_job_data))
        return job_list

    code = job_data.get("code")

    # Grab provision information from the code
    header = get_yaml_header(code)
    provision_header = header.get("required_packages")
    if provision_header:
        provision = build_provision_code(provision_header)

    if job_data.get("skip_provision"):
        provision = 'echo "skipping provisioning"'

    title = header.get("title")

    base_url = job_data.get("base_url")

    job = models.ModelRun(
        status=models.ModelRun.status_choices["created"],
        inputs=job_data.get("inputs", {}),
        backend="savio",
        base_url=base_url,
        title=title,
        code=code,
        provision=provision,
        created_by=created_by,
    )
    job.save()

    return [job]
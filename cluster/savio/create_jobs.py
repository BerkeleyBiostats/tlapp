from cluster.parse_notebook import get_yaml_header
from cluster.provision_code_generator import build_provision_code
from core import models

def create_jobs(created_by, job_data, parent=None):

    inputs = job_data.get("inputs", {})
    code = job_data.get("code")
    header = get_yaml_header(code)
    title = header.get("title")
    base_url = job_data.get("base_url")

    # Grab provision information from the code
    provision_header = header.get("required_packages")
    if provision_header:
        provision = build_provision_code(provision_header)

    if job_data.get("skip_provision"):
        provision = 'echo "skipping provisioning"'

    # Create multiple jobs if `job_data["inputs"]` is a list with a parent
    # job to group them together.
    if isinstance(inputs, list):

        parent_job = models.ModelRun(
            status=models.ModelRun.status_choices["created"],
            inputs=inputs,
            backend="savio",
            base_url=base_url,
            title=title,
            code="This is a parent job only responsible for provisioning",
            provision=provision,
            created_by=created_by,
            is_batch=True
        )
        parent_job.save()

        job_list = []
        for inputs_dict in inputs:
            single_job_data = job_data.copy()
            single_job_data["inputs"] = inputs_dict
            job_list.extend(create_jobs(created_by, single_job_data, parent=parent_job))

        return {
            "parent": parent_job,
            "children": job_list
        }

    provision = 'echo "skipping provisioning because this is a child job"'

    job = models.ModelRun(
        status=models.ModelRun.status_choices["created"],
        inputs=job_data.get("inputs", {}),
        backend="savio",
        base_url=base_url,
        title=title,
        code=code,
        provision=provision,
        created_by=created_by,
        parent=parent
    )
    job.save()

    return [job]
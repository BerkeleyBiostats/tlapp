from django.core.cache import cache
from cluster.parse_notebook import get_yaml_header
from cluster.provision_code_generator import build_provision_code
from core import models

def create_jobs(created_by, job_data):

    inputs = job_data.get("inputs", {})

    ghap_username = None
    ghap_password = None
    ghap_ip = None

    if "ghap_credentials" in job_data:
        ghap_credentials = job_data["ghap_credentials"]
        ghap_username = ghap_credentials["username"]
        ghap_password = ghap_credentials["password"]
        ghap_ip = ghap_credentials["ip"]

    if "r_packages" in job_data:
        job_data["provision"] = build_provision_code(job_data["r_packages"])

    if "model_template" in job_data:
        template = models.AnalysisTemplate.objects.get(pk=job_data["model_template"])
        code = template.code
        provision = template.provision
    else:
        code = job_data.get("code")
        provision = job_data.get("provision")

    # Override provision with anything in the code header
    # (Consider removing the ability to specify `required_packages` in
    # inputs.json)
    header = get_yaml_header(code)
    provision_header = header.get("required_packages")
    if provision_header:
        provision = build_provision_code(provision_header)

    title = header.get("title")

    if job_data.get("skip_provision"):
        provision = 'echo "skipping provisioning"'

    # Create multiple jobs if `job_data["inputs"]` is a list
    if isinstance(inputs, list):

        parent_job = models.ModelRun(
            status=models.ModelRun.status_choices["created"],
            inputs=inputs,
            backend="ghap",
            title=title,
            code=code,
            provision=provision,
            created_by=created_by,
            is_batch=True
        )
        parent_job.save()

        job_list = []
        for inputs_dict in inputs:
            single_job_data = job_data.copy()
            single_job_data["inputs"] = inputs_dict
            job_list.extend(create_jobs(created_by, single_job_data))
        return {
            "parent": parent_job,
            "children": job_list
        }

    job = models.ModelRun(
        dataset_id=job_data.get("dataset", None),
        status=models.ModelRun.status_choices["queued"],
        inputs=job_data["inputs"],
        backend=job_data["backend"],
        ghap_username=ghap_username,
        ghap_ip=ghap_ip,
        base_url=job_data.get("base_url"),
        title=title,
        code=code,
        provision=provision,
        created_by=created_by,
    )
    job.save()

    if ghap_password:
        # expire saved password after a day to reduce impact of the
        # application being compromised
        cache.set("ghap_password_%s" % job.id, ghap_password, timeout=60 * 60 * 24)

    return [job]


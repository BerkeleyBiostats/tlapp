# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import json
import yaml
import re

from django.db import transaction
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from core import models, tasks
import cluster


@login_required
def token(request):
    context = {"token": models.Token.objects.filter(user=request.user).first()}
    return render(request, "token.html", context)


def convert_params(name, defn):
    kind = defn.get("input")
    mapping = {"numeric": "int", "checkbox": "boolean", "select": "select"}

    defn["name"] = name
    defn["type"] = mapping.get(kind)
    defn["default"] = defn.get("value")

    return defn


def extract_fields(code):
    header = get_yaml_header(code)
    try:
        params = header["params"]["script_params"]["value"]
    except:
        return None
    inputs = [convert_params(n, d) for n, d in params.items()]
    return inputs


def extract_roles(code):
    header = get_yaml_header(code)
    try:
        return header["params"]["roles"]["value"]
    except:
        return ["W", "A", "Y", "-"]


@login_required
def index(request):

    return redirect('jobs')

    templates = models.AnalysisTemplate.objects.all()

    templates_json = [
        {
            "id": template.id,
            "name": template.name,
            "code": template.code,
            "fields": template.fields,
            "needsDataset": template.needs_dataset,
        }
        for template in templates
    ]

    for template in templates_json:
        fields = extract_fields(template["code"])
        if fields:
            template["fields"] = fields

        template["roles"] = extract_roles(template["code"])

    datasets = models.Dataset.objects.all()

    datasets_json = [
        {
            "id": dataset.id,
            "title": dataset.title,
            "url": dataset.url,
            "variables": dataset.variables["names"],
        }
        for dataset in datasets
    ]

    context = {
        "templates": templates,
        "templates_json": json.dumps(templates_json),
        "datasets_json": json.dumps(datasets_json),
    }

    return render(request, "index.html", context)


def parse_id_comma_list(raw):
    if not raw:
        return None
    sp = raw.split(",")
    return [int(x) for x in sp]


def _jobs(request):
    response_format = request.GET.get("format")
    mode = request.GET.get("mode", "batch")

    ids = request.GET.get("ids")
    ids = parse_id_comma_list(ids)

    if request.user.is_superuser:
        jobs = models.ModelRun.objects
    else:
        jobs = models.ModelRun.objects.filter(created_by=request.user)

    if mode == "oneoff":
        jobs = jobs.filter(parent=None, is_batch=False)
    elif mode == "debug":
        jobs = jobs.filter(is_batch=False)
    else:
        jobs = jobs.filter(is_batch=True)

    if ids:
        jobs = jobs.filter(id__in=ids)

    jobs = jobs.order_by("-created_at")

    status_counts = {}
    for choice in models.ModelRun.status_choices.keys():
        status_counts[choice] = jobs.filter(status=choice).count()

    status_filter = request.GET.get("status")
    if status_filter:
        jobs = jobs.filter(status=status_filter)

    jobs = jobs.prefetch_related("created_by", "children")

    per_page = request.GET.get("per_page", 30)
    paginator = Paginator(jobs, per_page)
    page = request.GET.get("page")
    jobs = paginator.get_page(page)

    context = {
        "jobs": jobs,
        "superuser": request.user.is_superuser,
        "status_counts": status_counts,
        "status_filter": status_filter,
        "mode": mode
    }

    if response_format == "json":
        # TODO: add the rest of pagination
        return JsonResponse({"jobs": [job.as_dict() for job in jobs]})
    else:
        return render(request, "jobs.html", context)



@csrf_exempt
def jobs(request):
    if request.user.is_authenticated or check_token(request):
        return _jobs(request)
    else:
        return unauthorized_reponse()

def update_job(job, job_data):
    # TODO: validate the status
    job.status = job_data.get("status")
    job.save()


@login_required
@csrf_exempt
def job_detail(request, job_id):
    response_format = request.GET.get("format")
    job = models.ModelRun.objects.get(pk=job_id)

    if request.method == "POST":
        job_data = json.loads(request.body.decode("utf-8"))
        update_job(job, job_data)
        return JsonResponse({"job": job.as_dict()})

    if response_format == "json":
        return JsonResponse(job.as_dict())

    context = {"job": job, "inputs_formatted": json.dumps(job.inputs, indent=2)}

    if job.has_children():
        status_counts = {}
        for choice in models.ModelRun.status_choices.keys():
            status_counts[choice] = job.status_count(choice)
        context["status_counts"] = status_counts

        child_jobs = job.children
        status_filter = request.GET.get("status")
        if status_filter:
            child_jobs = child_jobs.filter(status=status_filter)
        context["child_jobs"] = child_jobs.all()
        context["status_filter"] = status_filter

    if job.has_children():
        return render(request, "job_detail_parent.html", context)
    else:
        return render(request, "job_detail.html", context)


@login_required
def job_output(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    context = {"job": job}
    return render(request, "job_output.html", context)


@login_required
def _job_logs(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    context = {"job": job}

    return JsonResponse({"logs": job.output, "status": job.status}, safe=False)


@login_required
@csrf_exempt
def job_logs(request, job_id):
    return _job_logs(request, job_id)


@csrf_exempt
def job_logs_token(request, job_id):
    if check_token(request):
        return _job_logs(request, job_id)
    else:
        return unauthorized_reponse()


@login_required
def _job_status(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    context = {"job": job}

    return JsonResponse(job.status, safe=False)


@csrf_exempt
def job_status_token(request, job_id):
    if check_token(request):
        return _job_status(request, job_id)
    else:
        return unauthorized_reponse()


@login_required
def job_view_logs(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    context = {"job": job}

    return render(request, "job_logs.html", context)


def job_output_download(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    outputs_dir = "/tmp/outputs"
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
    with open(os.path.join(outputs_dir, "bar.txt"), "w") as f:
        f.write("hello")
    return redirect("/static/bar.txt")


def _job_download_url(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    return JsonResponse(job.output_url, safe=False)


@csrf_exempt
def job_download_url_token(request, job_id):
    if check_token(request):
        return _job_download_url(request, job_id)
    else:
        return unauthorized_reponse()


def _submit_job(request):
    job_data = json.loads(request.body.decode("utf-8"))

    if job_data["backend"] == "savio":
        jobs = cluster.savio.create_jobs(request.user, job_data)
        cluster.savio.submit_jobs(
            jobs, 
            job_data["savio_credentials"]["username"],
            job_data["savio_credentials"]["password"]
        )
    else:
        jobs = cluster.ghap.create_jobs(request.user, job_data)

    if isinstance(jobs, list):
        job = jobs[0]
    else:
        job = jobs["parent"]

    response = job.as_dict()
    response["results_url"] = request.build_absolute_uri(response["results_url"])
    response["job_id"] = job.id

    return JsonResponse(response, safe=False)


@login_required
@csrf_exempt
def submit_job(request):
    return _submit_job(request)


@csrf_exempt
def submit_job_token(request):
    if check_token(request):
        return _submit_job(request)
    else:
        return unauthorized_reponse()


def _append_log(request, job_id):
    log_lines = request.body.decode("utf-8")
    job = models.ModelRun.objects.get(pk=job_id)
    if job.output is None:
        job.output = log_lines
    else:
        job.output = job.output + log_lines
    job.save(update_fields=["output"])
    return JsonResponse({"status": "success"}, safe=False)


@csrf_exempt
def append_log_token(request, job_id):
    if check_token(request):
        return _append_log(request, job_id)
    else:
        return unauthorized_reponse()


def _finish_job(request, job_id):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        data = {}
    job = models.ModelRun.objects.get(pk=job_id)
    if data.get("status") == "error":
        job.status = models.ModelRun.status_choices["error"]
    else:
        job.status = models.ModelRun.status_choices["executed"]
    job.save()
    return JsonResponse({"status": job.status}, safe=False)


@csrf_exempt
def finish_job(request, job_id):
    if request.user.is_authenticated or check_token(request):
        return _finish_job(request, job_id)
    else:
        return unauthorized_reponse()


def _restart_job(request, job_id):
    job = models.ModelRun.objects.get(pk=job_id)
    job.status = models.ModelRun.status_choices["queued"]
    job.save()
    return JsonResponse({"status": "success"}, safe=False)


@csrf_exempt
def restart_job(request, job_id):
    if request.user.is_authenticated or check_token(request):
        return _restart_job(request, job_id)
    else:
        return unauthorized_reponse()


def unauthorized_reponse():
    return HttpResponse("Unauthorized", status=401)


def check_token(request):
    if "HTTP_AUTHORIZATION" not in request.META:
        print("Failed to find Authorization header")
        return False
    token = request.META["HTTP_AUTHORIZATION"]
    token = models.Token.objects.filter(token=token).first()
    if not token:
        print("Token didn't match")
        return False
    request.user = token.user
    return True


def _templates(request):
    # TODO: don't assume it's a POST request
    script_contents = request.body.decode("utf-8")

    header = get_yaml_header(script_contents)

    name = header["title"]
    provision = header.get("required_packages")
    template = models.AnalysisTemplate.objects.filter(name=name).first()

    if template is None:
        template = models.AnalysisTemplate()

    template.name = name
    template.fields = None
    template.code = script_contents
    template.needs_dataset = True
    template.provision = build_provision_code(provision)
    template.save()

    return JsonResponse(
        {
            "success": True,
            "url": request.build_absolute_uri("/?initialChoice=%s" % template.id),
        },
        safe=False,
    )


@csrf_exempt
def templates(request):
    if check_token(request):
        return _templates(request)
    else:
        return unauthorized_reponse()

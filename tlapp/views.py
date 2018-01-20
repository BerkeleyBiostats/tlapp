# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import json

from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from core import models, tasks

@login_required
def token(request):
	context = {
		"token": models.Token.objects.filter(user=request.user).first()
	}
	return render(request, 'token.html', context)

@login_required
def index(request):

	templates = models.AnalysisTemplate.objects.all()

	templates_json = [{
		"id": template.id,
		"name": template.name,
		"code": template.code,
		"fields": template.fields,
		"needsDataset": template.needs_dataset,
	} for template in templates]

	datasets = models.Dataset.objects.all()

	datasets_json = [{
		"id": dataset.id,
		"title": dataset.title,
		"url": dataset.url,
		"variables": dataset.variables['names'],
	} for dataset in datasets]

	context = {
		"templates": templates,
		"templates_json": json.dumps(templates_json),
		"datasets_json": json.dumps(datasets_json),
	}

	return render(request, 'index.html', context)

@login_required
def jobs(request):
	jobs = models.ModelRun.objects.filter(created_by=request.user).order_by('-created_at')
	context = {
		"jobs": jobs,
	}
	return render(request, 'jobs.html', context)

def job_detail(request, job_id):
	job = models.ModelRun.objects.get(pk=job_id)
	context = {
		"job": job,
		"inputs_formatted": json.dumps(job.inputs, indent=2),
	}
	return render(request, 'job_detail.html', context)

def job_output_download(request, job_id):
	job = models.ModelRun.objects.get(pk=job_id)
	outputs_dir = '/tmp/outputs'
	if not os.path.exists(outputs_dir):
		os.makedirs(outputs_dir)
	with open(os.path.join(outputs_dir, 'bar.txt'), 'w') as f:
		f.write('hello')
	return redirect('/static/bar.txt')

def expand_r_package_definition(package_definition):
    if package_definition.startswith("github://"):
        full_package_name = package_definition[len("github://"):]
        package_name = full_package_name.split("/")[-1]
        output = "R -e \"if (!require('%s')) devtools::install_github('%s')\"" % (package_name, full_package_name)
    elif "@" in package_definition:
        package_name, version = package_definition.split("@")
        output = "R -e \"if (!require('%s')) devtools::install_version('%s', version='%s', repos = 'http://cran.rstudio.com/')\"" % (package_name, package_name, version)
    else:
        package_name = package_definition
        output = "R -e \"if (!require('%s')) install.packages('%s', repos = 'http://cran.rstudio.com/')\"" % (package_name, package_name)

    return output

def build_provision_code(r_packages_section):
    create_directories = """

mkdir -p "/data/R/x86_64-redhat-linux-gnu-library/3.2/"
mkdir -p "/data/R/x86_64-redhat-linux-gnu-library/3.4/"

"""
    return create_directories + "\n".join([expand_r_package_definition(pd) for pd in r_packages_section])

def _submit_job(request):
	job_data = json.loads(request.body.decode('utf-8'))

	ghap_username = None
	ghap_password = None
	ghap_ip = None
	if 'ghap_credentials' in job_data:
		ghap_credentials = job_data['ghap_credentials']
		ghap_username = ghap_credentials['username']
		ghap_password = ghap_credentials['password']
		ghap_ip = ghap_credentials['ip']

	if 'r_packages' in job_data:
		job_data['provision'] = build_provision_code(job_data['r_packages'])

	job = models.ModelRun(
		model_template_id = job_data.get('model_template', None),
		dataset_id = job_data.get('dataset', None),
		status = models.ModelRun.status_choices['submitted'],
		inputs = job_data['inputs'],
		backend = job_data['backend'],
		ghap_username = ghap_username,
		ghap_ip = ghap_ip,
		code = job_data.get('code', None),
		provision = job_data.get('provision', None),
		created_by = request.user,
	)
	job.save()

	if ghap_password:
		# expire saved password after a day to reduce impact of the 
		# application being compromised
		cache.set("ghap_password_%s" % job.id, ghap_password, timeout=60*60*24)

	ret = job.as_dict()
	ret['results_url'] = request.build_absolute_uri(ret['results_url'])

	return JsonResponse(ret, safe=False)


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
	log_lines = request.body.decode('utf-8')
	job = models.ModelRun.objects.get(pk=job_id)
	job.output = job.output + log_lines
	job.save()
	return JsonResponse({"status": "success"}, safe=False)

@csrf_exempt
def append_log_token(request, job_id):
	if check_token(request):
		return _append_log(request, job_id)
	else:
		return unauthorized_reponse()

def _finish_job(request, job_id):
	job_data = json.loads(request.body.decode('utf-8'))
	job = models.ModelRun.objects.get(pk=job_id)

	job.status = models.ModelRun.status_choices['success']
	job.save()

	# TODO: will need to queue this if takes longer than 30s
	tasks.post_process_outputs(job)
	job.save()

	return JsonResponse({"status": "success"}, safe=False)

@csrf_exempt
def finish_job(request, job_id):
	if check_token(request):
		return _finish_job(request, job_id)
	else:
		return unauthorized_reponse()

def unauthorized_reponse():
	return HttpResponse('Unauthorized', status=401)

def check_token(request):
	if 'HTTP_AUTHORIZATION' not in request.META:
		print("Failed to find Authorization header")
		return False
	token = request.META['HTTP_AUTHORIZATION']
	print("Authorization header %s" % token)
	token = models.Token.objects.filter(token=token).first()
	if not token:
		print("Token didn't match")
		return False
	request.user = token.user
	return True






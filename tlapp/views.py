# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import json

from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from core import models

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






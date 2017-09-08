# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from core import models

# @login_required
def index(request):

	templates = models.ModelTemplate.objects.all()

	templates_json = [{
		"id": template.id,
		"name": template.name,
		"code": template.code,
		"fields": template.fields
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

# @login_required
def jobs(request):
	jobs = models.ModelRun.objects.all().order_by('-created_at')
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

# @login_required
@csrf_exempt
def submit_job(request):
	job_data = json.loads(request.body)

	job = models.ModelRun(
		model_template_id = job_data['model_template'],
		status = models.ModelRun.status_choices['submitted'],
		inputs = job_data['inputs'],
	)

	# Hardcode this for now
	job.inputs['params'] = {
		"learners": {
			"glm_learner": {
				"learner": "Lrnr_glm_fast"
			},
			
			"sl_glmnet_learner": {
				"learner": "Lrnr_pkg_SuperLearner",
				"params": {
					"SL_wrapper":"SL.glmnet"
				}
			}
			
		},
		"metalearner": {
			"learner": "Lrnr_nnls"
		}
	}

	# nodes.Y and nodes.A expect a single element
	if len(job.inputs['data']['nodes']['Y']) == 1:
		job.inputs['data']['nodes']['Y'] = job.inputs['data']['nodes']['Y'][0]
	if len(job.inputs['data']['nodes']['A']) == 1:
		job.inputs['data']['nodes']['A'] = job.inputs['data']['nodes']['A'][0]

	job.save()

	return JsonResponse(job.as_dict())





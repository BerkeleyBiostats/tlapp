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
		"parameters": template.parameters
	} for template in templates]

	context = {
		"templates": templates,
		"templates_json": json.dumps(templates_json),
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
	}
	return render(request, 'job_detail.html', context)

# @login_required
@csrf_exempt
def submit_job(request):
	job_data = json.loads(request.body)

	job = models.ModelRun(
		model_template_id = job_data['model_template'],
		status = models.ModelRun.status_choices['submitted'],
		parameters = job_data['parameters'],
	)
	job.save()

	return JsonResponse(job.as_dict())





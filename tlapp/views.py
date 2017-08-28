# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from core import models

# @login_required
def index(request):

	templates = models.ModelTemplate.objects.all()

	templates_json = [{
		"name": template.name,
		"code": template.code,
		"parameters": template.parameters
	} for template in templates]

	context = {
		"templates": templates,
		"templates_json": json.dumps(templates_json),
	}

	return render(request, 'index.html', context)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

# @login_required
def index(request):

	model_parameters = {
		"parameters": [{
			"name": "ABar",
			"type": "float",
			"help": "A block of help text that explains the model input.",
		}, {
			"name": "Learners",
			"type": "enum",
			"choices": [
				"GLM",
				"Random Forest",
				"Regression"
			],
		},]

	}

	context = {
		"variables": [
			"studyid",
			"subjid",
			"siteid",
			"sex",
			"agedays",
			"WHZ",
			"region",
			"risk factor"
		]
	}

	return render(request, 'index.html', context)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.AnalysisTemplate)
admin.site.register(models.Dataset)
admin.site.register(models.Token)


@admin.register(models.ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
	fields = (
		"created_by",
		"status",
		"backend",
		"ghap_username",
		"ghap_ip",
		"base_url",
		"title",
		"output_url",
		"traceback",
		"model_template",
		"dataset",
		"postprocessing_attempts",
		"postprocessing_attempted_at",
		"postprocessing_traceback",
		"is_batch",
		"last_heartbeat",
		"inputs",
		"code",
		"provision",
	)

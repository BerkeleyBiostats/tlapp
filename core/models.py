# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models

class Dataset(models.Model):
	title = models.CharField(max_length=256)
	url = models.URLField(null=True, blank=True)
	variables = JSONField(null=True, blank=True)

class ModelTemplate(models.Model):
	name = models.CharField(max_length=256)
	parameters = JSONField(null=True, blank=True)
	code = models.TextField(null=True, blank=True)

	def __str__(self):
		return self.name

class ModelRun(models.Model):

	status_choices = {
		'submitted': 'submitted',
		'running': 'running',
		'success': 'success',
		'error':' error',
	}

	created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
	parameters = JSONField(null=True, blank=True)
	status = models.CharField(max_length=32)
	output = models.TextField(null=True, blank=True)
	output_zip = models.BinaryField(null=True, blank=True) # TODO: remove this, unused
	traceback = models.TextField(null=True, blank=True)
	model_template = models.ForeignKey(ModelTemplate)

	def __str__(self):
		return "%s %s" % (self.model_template.name, self.created_at)

	def as_dict(self):
		return {
			'status': self.status,
			'created_at': self.created_at,
			'model_template': self.model_template.name,
		}
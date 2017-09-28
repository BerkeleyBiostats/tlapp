# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models

class Dataset(models.Model):
	title = models.CharField(max_length=256)
	url = models.URLField(null=True, blank=True)
	variables = JSONField(null=True, blank=True)

	# Path to file if it's in a GHAP git repo
	repository_path = models.TextField(max_length=256, null=True, blank=True)

	def __str__(self):
		return self.title


class ModelTemplate(models.Model):
	name = models.CharField(max_length=256)
	fields = JSONField(null=True, blank=True)
	code = models.TextField(null=True, blank=True)
	provision = models.TextField(null=True, blank=True)

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
	inputs = JSONField(null=True, blank=True)
	status = models.CharField(max_length=32)
	backend = models.CharField(max_length=32, blank=True, null=True)
	ghap_username = models.CharField(max_length=256, blank=True, null=True)
	ghap_ip = models.CharField(max_length=256, blank=True, null=True)
	output = models.TextField(null=True, blank=True)
	output_zip = models.BinaryField(null=True, blank=True) # TODO: remove this, unused
	output_url = models.URLField(null=True, blank=True)
	traceback = models.TextField(null=True, blank=True)
	model_template = models.ForeignKey(ModelTemplate)
	dataset = models.ForeignKey(Dataset, null=True, blank=True)

	def __str__(self):
		return "%s %s" % (self.model_template.name, self.created_at)

	def as_dict(self):
		return {
			'status': self.status,
			'created_at': self.created_at,
			'model_template': self.model_template.name,
		}
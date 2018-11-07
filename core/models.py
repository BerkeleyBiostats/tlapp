# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

def get_user_running_job_count(self):
	return ModelRun.objects.filter(
		created_by=self, 
		status=ModelRun.status_choices['running']
	).count()

User.add_to_class("running_job_count", get_user_running_job_count)

class Token(models.Model):
	user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
	token = models.CharField(max_length=128)

	def __str__(self):
		return "%s %s" % (self.user.email, self.token)

class Dataset(models.Model):
	title = models.CharField(max_length=256)
	url = models.URLField(null=True, blank=True)
	variables = JSONField(null=True, blank=True)

	# Path to file if it's in a GHAP git repo
	repository_path = models.TextField(max_length=256, null=True, blank=True)

	def __str__(self):
		return self.title


class AnalysisTemplate(models.Model):
	name = models.CharField(max_length=256)
	fields = JSONField(null=True, blank=True)
	code = models.TextField(null=True, blank=True)
	provision = models.TextField(null=True, blank=True)
	needs_dataset = models.BooleanField(default=True)

	def __str__(self):
		return self.name

class ModelRun(models.Model):

	status_choices = {
		'created': 'created',
		'queued': 'queued',
		'submitted': 'submitted',
		'running': 'running',
		'executed': 'executed',
		'postprocessing': 'postprocessing',
		'error': 'error',
		'success': 'success',
	}

	created_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
	created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
	inputs = JSONField(null=True, blank=True)
	status = models.CharField(max_length=32)
	backend = models.CharField(max_length=32, blank=True, null=True)
	ghap_username = models.CharField(max_length=256, blank=True, null=True)
	ghap_ip = models.CharField(max_length=256, blank=True, null=True)
	base_url = models.CharField(max_length=256, blank=True, null=True)
	title = models.CharField(max_length=256, blank=True, null=True)
	output = models.TextField(null=True, blank=True)
	output_zip = models.BinaryField(null=True, blank=True) # TODO: remove this, unused
	output_url = models.URLField(null=True, blank=True)
	report_html = models.TextField(null=True, blank=True)	
	traceback = models.TextField(null=True, blank=True)
	model_template = models.ForeignKey(AnalysisTemplate, null=True, blank=True, on_delete=models.SET_NULL)
	dataset = models.ForeignKey(Dataset, null=True, blank=True, on_delete=models.SET_NULL)
	postprocessing_attempted_at = models.DateTimeField(blank=True, null=True)
	postprocessing_traceback = models.TextField(null=True, blank=True)
	is_batch = models.BooleanField(default=False)
	parent = models.ForeignKey("ModelRun", null=True, blank=True, on_delete=models.CASCADE, related_name="children")


	# Support pushing code instead of model template for one-off runs
	code = models.TextField(null=True, blank=True)
	provision = models.TextField(null=True, blank=True)


	def __str__(self):
		if self.model_template:
			return "%s %s" % (self.model_template.name, self.created_at)
		else:
			return "One-off %s" % (self.created_at)

	def has_children(self):
		return self.children.count() > 0

	def child_count(self):
		return self.children.count()

	def status_count(self, status):
		return self.children.filter(status=self.status_choices[status]).count()

	def created_count(self):
		return self.status_count(self.status_choices["created"])

	def running_count(self):
		return self.status_count(self.status_choices["running"])

	def success_count(self):
		return self.status_count(self.status_choices["success"])

	def as_dict(self):
		ret = {
			'status': self.status,
			'created_at': self.created_at,
			'results_url': reverse('job_detail', args=[self.id])
		}
		if self.model_template is not None:
			ret['model_template'] = self.model_template.name
		if self.has_children:
			ret['jobs'] = [job.as_dict() for job in self.children.all()]
		return ret

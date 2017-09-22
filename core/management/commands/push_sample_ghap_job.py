import os
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.cache import cache
from core import models

class Command(BaseCommand):
    help = "Push a sample job for testing GHAP integration"

    def handle(self, *args, **options):
        mt = models.ModelTemplate.objects.get(name='sl3_sample.R')
        job = models.ModelRun(
            model_template = mt,
            status = models.ModelRun.status_choices['submitted'],
            inputs = {},
            backend = 'ghap',
            ghap_username = os.environ.get('GHAP_USERNAME'),
            ghap_ip = os.environ.get('GHAP_IP'),
        )
        job.save()

        cache.set('ghap_password_%s' % job.id, os.environ.get('GHAP_PASSWORD'), timeout=24*60*60)
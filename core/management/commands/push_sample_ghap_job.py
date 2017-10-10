import os
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.cache import cache
from core import models

sample_inputs = {
    "fields": [
        {"name": "Learners", "value": []}, 
        {"name": "Abar"}
    ], 
    "data": {
        "nodes": {"A": "parity", "Y": "haz", "W": ["apgar1", "apgar5", "gagebrth", "mage", "meducyrs", "sexn"]}, 
        "type": "csv", 
        "uri": "https://raw.githubusercontent.com/BerkeleyBiostats/tlapp/30821fe37d9fdb2cb645ad2c42f63f1c1644d7c4/cpp.csv"
    }, 
    "params": {}
}

class Command(BaseCommand):
    help = "Push a sample job for testing GHAP integration"

    def handle(self, *args, **options):
        mt = models.AnalysisTemplate.objects.get(name='sl3_sample.R')
        job = models.ModelRun(
            model_template = mt,
            status = models.ModelRun.status_choices['submitted'],
            inputs = sample_inputs,
            backend = 'ghap',
            ghap_username = os.environ.get('GHAP_USERNAME'),
            ghap_ip = os.environ.get('GHAP_IP'),
            dataset = models.Dataset.objects.get(title="ki1000306-ZincSGA"),
        )
        job.save()

        cache.set('ghap_password_%s' % job.id, os.environ.get('GHAP_PASSWORD'), timeout=24*60*60)
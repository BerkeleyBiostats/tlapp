import logging
import time
from django.core.management.base import BaseCommand
from core import tasks

logger = logging.getLogger('django')

class Command(BaseCommand):
	help = "Worker for db jobs"

	def handle(self, *args, **options):
		logger.info("Booting up worker")
		while True:
			count = tasks.handle_jobs()
			if count == 0:
				time.sleep(1)
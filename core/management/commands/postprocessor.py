import logging
import time
from django.core.management.base import BaseCommand
from core import postprocessor

logger = logging.getLogger('django')

class Command(BaseCommand):
	help = "Worker for postprocessing"

	def handle(self, *args, **options):
		logger.info("Booting up postprocessor")
		while True:
			count = postprocessor.handle_a_job()
			if count == 0:
				time.sleep(1)
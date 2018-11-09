import datetime
from datetime import timedelta
import logging
import os
from django.conf import settings
from core import models
import cluster.ghap

logger = logging.getLogger("django")


def reap_stalled_jobs():
    five_minutes_ago = datetime.datetime.utcnow() - timedelta(minutes=5)
    stalled_jobs = models.ModelRun.objects.filter(
        last_heartbeat__lte=five_minutes_ago,
        status=models.ModelRun.status_choices["running"],
    )
    for job in stalled_jobs.all():
        job.status = models.ModelRun.status_choices["error"]
        job.traceback = "Job run stalled (heartbeat check)"
        job.save(update_fields=["status", "traceback"])


def push_a_ghap_job():
    # Pick off a random ModelRun job
    job = (
        models.ModelRun.objects.filter(status=models.ModelRun.status_choices["queued"])
        .order_by("?")
        .first()
    )

    if job is None:
        return 0

    if job.created_by.running_job_count() >= settings.MAX_CONCURRENT_JOBS:
        return 0

    cluster.ghap.submit_jobs([job])

    return 1


def handle_jobs():
    reap_stalled_jobs()
    jobs_pushed = push_a_ghap_job()
    return jobs_pushed

from contextlib import redirect_stdout, redirect_stderr
import io
import logging
import datetime
import traceback
from core import models

logger = logging.getLogger("django")

class StreamingStringIO(io.StringIO):
    def __init__(self, job):
        self.job = job
        io.StringIO.__init__(self)

    def write(self, s):
        io.StringIO.write(self, s)
        self.job.output = self.getvalue()
        self.job.save()

def run_job(runner, job):
    job.status = models.ModelRun.status_choices["running"]
    job.last_heartbeat = datetime.datetime.utcnow()
    job.save(update_fields=["status", "last_heartbeat"])

    f = StreamingStringIO(job)

    with redirect_stdout(f), redirect_stderr(f):
        try:
            runner(job)
        except:
            logger.info(traceback.format_exc())
            job.status = models.ModelRun.status_choices["error"]

    job.save()
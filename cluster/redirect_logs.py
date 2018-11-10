from contextlib import redirect_stdout, redirect_stderr, contextmanager
import io
import logging
import datetime
import traceback
from core import models

logger = logging.getLogger("django")

@contextmanager
def redirect_logs(job):
    f = StreamingStringIO(job)
    with redirect_stdout(f), redirect_stderr(f):
        try:
            yield
        except:
            logger.info(traceback.format_exc())
            job.status = models.ModelRun.status_choices["error"]

class StreamingStringIO(io.StringIO):
    def __init__(self, job):
        self.job = job
        io.StringIO.__init__(self)

    def write(self, s):
        io.StringIO.write(self, s)
        self.job.output = self.getvalue()
        self.job.save(update_fields=["output"])

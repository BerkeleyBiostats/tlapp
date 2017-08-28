from core import models

def handle_jobs():
	# Pick off a random ModelRun job
	job = models.ModelRun.objects.filter(
		status=models.ModelRun.status_choices['submitted'],
	).first()

	if job is None:
		return 0

	job.status = models.ModelRun.status_choices['running']
	job.save()

	# TODO: run the job

	job.status = models.ModelRun.status_choices['success']
	job.save()

	return 1
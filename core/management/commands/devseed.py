from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core import models

class Command(BaseCommand):
    help = "Initialize the app for development"

    def handle(self, *args, **options):
        user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'admin')
        user.save()

        parameters = {
            "fields": [{
                "name": "ABar",
                "type": "float",
                "help": "A block of help text that explains the model input.",
            }, {
                "name": "Learners",
                "type": "enum",
                "choices": [
                    "GLM",
                    "Random Forest",
                    "Regression"
                ],
            }, {
                "name": "Spacing",
                "type": "enum",
                "choices": [
                    "tight",
                    "loose",
                ],
            },]
        }

        code = """
            print('hello world')
        """

        mt = models.ModelTemplate(
            name='HGCKki_sample.R',
            parameters=parameters,
            code=code
        )   
        mt.save()

        parameters = {
            "fields": [{
                "name": "Spacing",
                "type": "enum",
                "choices": [
                    "tight",
                    "loose",
                ],
            },]
        }

        code = """
            print('foo')
        """

        mt2 = models.ModelTemplate(
            name='Another sample.R',
            parameters=parameters,
            code=code
        )
        mt2.save()

        job = models.ModelRun(
            model_template=mt,
            status=models.ModelRun.status_choices['submitted'],
        )
        job.save()

        job = models.ModelRun(
            model_template=mt2,
            status=models.ModelRun.status_choices['submitted'],
        )
        job.save()

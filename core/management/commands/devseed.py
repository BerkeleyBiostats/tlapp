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
            "parameters": [{
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


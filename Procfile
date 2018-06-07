web: newrelic-admin run-program gunicorn tlapp.wsgi --log-file -
worker: python manage.py worker
release: python manage.py migrate
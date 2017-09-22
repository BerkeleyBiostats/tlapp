Targeted Learning App
===

Install

	pip install -r requirements.txt

Run

	python manage.py runserver

Push a sample ghap job and run the worker:
	
	export GHAP_IP=...
	export GHAP_PASSWORD=...
	export GHAP_USERNAME=...
	python manage.py push_sample_ghap_job
	python manage.py worker
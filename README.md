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

Workflow for Analysis Templates
---

From RStudio: Copy the Analysis Template's `code` field into RStudio, then run "Knit with Parameters".

From the command line: 

	Rscript runner.R <code_filename.R> <params_filename.json> <output_filename.md>

Creative Commons Credits
---

Bow Icon: bow by Milky - Digital innovation from the Noun Project
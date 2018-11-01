export TLAPP_TOKEN={{ token }}
export TLAPP_LOGS_URL={{ logs_url }}

export R_LIBS_USER=$HOME/rlibs

echo "Making sure longbowtools package is available for runner"

R -e "if (!require('devtools')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"

echo "Running provision script"

./provision.sh

echo "Making sure longbowtools package is available for runner"

R -e "if (!require('longbowtools')) devtools::install_github('tlverse/longbowtools')"

echo "Starting analysis"

if {{ r_cmd }} ; then
	echo "Running analysis succeeded"

	cd /tmp
	tar -zcvf {{ tar_file }} {{ output_dir }}

	curl \
	  --request PUT \
	  --upload-file {{ tar_file }} \
	  "{{ put_url | safe }}"

	curl \
	  --request POST \
	  -H "Authorization: $TLAPP_TOKEN" \
	  -d "{}" \
	  "{{ finish_url | safe }}"

else
	echo "Running analysis failed"

	curl \
	  --request POST \
	  -H "Authorization: $TLAPP_TOKEN" \
	  -d '{"status": "error"}' \
	  "{{ finish_url | safe }}"

fi
export TLAPP_TOKEN={{ token }}
export TLAPP_LOGS_URL={{ logs_url }}
export R_LIBS_USER=$HOME/rlibs
export GITHUB_PAT={{ github_token }}

curl \
	--request POST \
	-H "Authorization: $TLAPP_TOKEN" \
	-d '{"status": "running"}' \
	"{{ job_url | safe }}"

echo "Making sure longbowtools package is available for runner"

mkdir -p ~/rlibs
R -e "if (!require('devtools')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"

{% block preprovision %}{% endblock %}


echo "Running provision script"

./provision.sh

echo "Making sure longbowtools package is available for runner"

module load pandoc-2.4
module load pandoc-1.17
module load gcc-4.9.4
module load python-3.5.2

R -e "if (!require('longbowtools')) devtools::install_github('tlverse/longbowtools')"

echo "Starting analysis"

if {{ r_cmd }} ; then
	echo "Running analysis succeeded"

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

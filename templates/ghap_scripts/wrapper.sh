export TLAPP_TOKEN={{ token }}
export TLAPP_LOGS_URL={{ logs_url }}


echo "Making sure longbowtools package is available for runner"

R -e "if (!require('devtools')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"
R -e "devtools::install_github('tlverse/longbowtools')"

echo "Running provision script"

./provision.sh

echo "Starting analysis"

{{ r_cmd }}

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
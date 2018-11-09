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

if [ ! -f ~/bin/pandoc ]; then
	echo "Installing pandoc"
	mkdir -p ~/downloads
	wget -O ~/downloads/pandoc-2.3.1-linux.tar.gz https://github.com/jgm/pandoc/releases/download/2.3.1/pandoc-2.3.1-linux.tar.gz
	tar xvzf ~/downloads/pandoc-2.3.1-linux.tar.gz -C ~/downloads
	cp ~/downloads/pandoc-2.3.1/bin/pandoc ~/bin
fi



echo "Running provision script"

./provision.sh

echo "Making sure longbowtools package is available for runner"

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
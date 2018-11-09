{% extends "cluster_scripts/wrapper.sh" %}

{% block preprovision %}

if [ ! -f ~/bin/pandoc ]; then
	echo "Installing pandoc"
	mkdir -p ~/downloads
	wget -O ~/downloads/pandoc-2.3.1-linux.tar.gz https://github.com/jgm/pandoc/releases/download/2.3.1/pandoc-2.3.1-linux.tar.gz
	tar xvzf ~/downloads/pandoc-2.3.1-linux.tar.gz -C ~/downloads
	cp ~/downloads/pandoc-2.3.1/bin/pandoc ~/bin
fi

{% endblock %}
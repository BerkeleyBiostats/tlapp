{% extends "cluster_scripts/wrapper.sh" %}

{% block preprovision %}

./ensure_git_dataset.sh

{% endblock %}
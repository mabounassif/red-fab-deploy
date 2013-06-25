# Customize this script if need to launch a configurable conf file. EI: -c `hostname`.py
{% block launch_config %}
{% endblock %}

{% block exec_command %}
exec {{ gunicorn_env_exec }} -c {{ gunicorn_python }} {{ settings_init }}
{% endblock %}

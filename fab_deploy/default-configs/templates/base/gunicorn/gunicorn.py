import os
{% block settings %}
pythonpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../project/'))
bind = {{ listen_address }}

# Make sure to tune
workers = {{ num_workers }}

loglevel = "WARNING"
logfile = {{ gunicorn_log_file }}
django_settings = "settings"
{% endblock %}

# Customize this script if need to launch a configurable conf file. EI: -c `hostname`.py
{% block def_command %}
COMMAND="{{ gunicorn_env_exec }} -D -c {{ gunicorn_python }} {{ settings_init }}"
{% endblock %}

{% block newrelic_setup %}
# New Relic enviroment variables - do NOT rename!
NEW_RELIC_ENVIRONMENT= {{ newrelic_env }}
NEW_RELIC_CONFIG_FILE= {{ newrelic_config }}
# New Relic startup script
NEW_RELIC_ADMIN= {{ newrelic_env_admin }}

if [ -f $NEW_RELIC_CONFIG_FILE ] && [ -f $NEW_RELIC_ADMIN ]
then
    export NEW_RELIC_ENVIRONMENT
    export NEW_RELIC_CONFIG_FILE
    exec $NEW_RELIC_ADMIN run-program $COMMAND
else
    exec $COMMAND
fi
{% endblock %}
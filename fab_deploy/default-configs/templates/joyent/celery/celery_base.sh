{% block get_args %}
getproparg() {
    val=`svcprop -p $1 $SMF_FMRI`
    [ -n "$val" ] && echo $val
}

if [ -z $SMF_FMRI ]; then
    echo "SMF framework variables are not initialized."
    exit $SMF_EXIT_ERR
fi
{% endblock %}

{% block defaults %}
DEFAULT_PID_FILE= "{{ default_celery_pid }}"
DEFAULT_LOG_FILE="{{ default_celery_log }}"
DEFAULT_LOG_LEVEL="INFO"
DEFAULT_PYTHON="python"
{% endblock %}

{% block globals %}
{% endblock %}

{% block newrelic_export %}
# New Relic enviroment variables - do NOT rename!
NEW_RELIC_ENVIRONMENT= {{ newrelic_env }}
NEW_RELIC_CONFIG_FILE= {{ newrelic_config }}
# New Relic startup script
NEW_RELIC_ADMIN= {{ newrelic_env_admin }}
{% endblock %}

{% block functiondefs %}

check_dev_null() {
    if [ ! -c /dev/null ]; then
        echo "/dev/null is not a character device!"
        exit 1
    fi
}
{% endblock %}

{% block process_arg %}
{% endblock %}
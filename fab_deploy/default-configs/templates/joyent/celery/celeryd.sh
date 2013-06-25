#!/bin/sh -e
# Adapted from https://github.com/ask/celery/blob/master/contrib/generic-init.d/
{% extends "joyent/celery/celery_base.sh" %}


{% block defaults %}
{{ super() }}
DEFAULT_NODES="celery"
DEFAULT_CONCURENCY="2"
DEFAULT_TIME_LIMIT="500"
DEFAULT_PYTHON="python"
{% endblock %}

{% block globals %}
CELERYD_PID_FILE=$(getproparg celeryd/pid_file)
CELERYD_LOG_FILE=$(getproparg celeryd/log_file)
CELERYD_LOG_LEVEL=$(getproparg celeryd/log_level)
CELERYD_NODES=$(getproparg celeryd/nodes)
CELERYD_CONCURENCY=$(getproparg celeryd/concurrency)
CELERYD_TIME_LIMIT=$(getproparg celeryd/time_limit)
PYTHON=$(getproparg celeryd/python)

CELERYD_PID_FILE=${CELERYD_PID_FILE:-$DEFAULT_PID_FILE}
CELERYD_LOG_FILE=${CELERYD_LOG_FILE:-$DEFAULT_LOG_FILE}
CELERYD_LOG_LEVEL=${CELERYD_LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
CELERYD_NODES=${CELERYD_NODES:-$DEFAULT_NODES}
CELERYD_CONCURENCY=${CELERYD_CONCURENCY:-$DEFAULT_CONCURENCY}
CELERYD_TIME_LIMIT=${CELERYD_TIME_LIMIT:-$DEFAULT_TIME_LIMIT}

COMMAND_PREFEX=$(getproparg celeryd/command_prefix)
CELERYD_MULTI="$PYTHON $COMMAND_PREFEX celeryd_multi"

CELERYD="-m celery.bin.celeryd_detach"
{% endblock %}

{% block newrelic_export %}
{{ super() }}
if [ -f $NEW_RELIC_CONFIG_FILE ] && [ -f $NEW_RELIC_ADMIN ]
then
    export NEW_RELIC_ENVIRONMENT
    export NEW_RELIC_CONFIG_FILE
    CELERYD_MULTI=$NEW_RELIC_ADMIN" run-program "$CELERYD_MULTI
fi
{% endblock %}

{% block functiondefs %}
{{ super() }}

stop_workers () {
    $CELERYD_MULTI stop $CELERYD_NODES --pidfile="$CELERYD_PID_FILE"
}


start_workers () {
    $CELERYD_MULTI start $CELERYD_NODES                     \
                           --pidfile="$CELERYD_PID_FILE"      \
                           --logfile="$CELERYD_LOG_FILE"      \
                           --loglevel="$CELERYD_LOG_LEVEL"    \
                           --cmd="$CELERYD"                   \
                           --time-limit="$CELERYD_TIME_LIMIT" \
                           --concurrency="$CELERYD_CONCURENCY"
}


restart_workers () {
    $CELERYD_MULTI restart $CELERYD_NODES                     \
                           --pidfile="$CELERYD_PID_FILE"      \
                           --logfile="$CELERYD_LOG_FILE"      \
                           --loglevel="$CELERYD_LOG_LEVEL"    \
                           --cmd="$CELERYD"                   \
                           --time-limit="$CELERYD_TIME_LIMIT" \
                           --concurrency="$CELERYD_CONCURENCY"
}
{% endblock %}


{% block process_arg %}
case "$1" in
    start)
        check_dev_null
        start_workers
    ;;

    stop)
        check_dev_null
        stop_workers
    ;;

    restart)
        check_dev_null
        restart_workers
    ;;

esac

exit 0
{% endblock %}

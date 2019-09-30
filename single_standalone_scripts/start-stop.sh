# /bin/bash

export JAVA_HOME="/..."
export PATH=$JAVA_HOME/bin:$PATH

TARGET_SERVER="$(hostname -s)";
ENVIRONMENT_NAME="Local";
CURRENT_DIRECTORY="$(dirname "$(readlink -f "$BASH_SOURCE")")";
PID="";

TIME_LIMIT_MINUTES=10;
MAX_ITERATIONS=5;
SLEEPING_TIME=5;

REQUIRED_USER="java_user";
LOG_DIRECTORY="/logs";

GREP_PHRASE="...jar";
TOOLNAME="${GREP_PHRASE};
EXECUTION="nohup java -jar ${TOOLNAME} &";



check_fail()
{
  local RETURNCODE=$1;
  local LINENUMBER=$2;
  local ERRORMESSAGE=$3;
  local ERRORCODE=$4;
  if [ ${RETURNCODE} -ne 0 ]
  then
    echo "ERROR Command in line $((LINENUMBER-1)) failed. Returncode: ${RETURNCODE}";
    echo "-Description: ${ERRORMESSAGE}";
    exit ${ERRORCODE}
  fi
  #echo "Checkpoint No. ${ERRORCODE}";
  return 0;
}

do_log()
{
  echo "INFO $(date +%T) [${ENVIRONMENT_NAME}-${TARGET_SERVER}]: $1"
  return 0
}

do_warn()
{
  echo "WARNING $(date +%T) [${ENVIRONMENT_NAME}-${TARGET_SERVER}]: $1";
  return 0
}

status ()
{
  ps -ef | grep -v "grep" | grep -qi "${GREP_PHRASE}"
  if [[ "$?" == "0" ]];
  then
    PID="$(ps -ef | grep -v "grep" | grep -i "${GREP_PHRASE}" | awk '{print $2}')";
    do_log "${TOOLNAME} is running. PID: ${PID}"
    return 0;
  else
    do_log "${TOOLNAME} is not running."
    return 1;
  fi
}

working_status ()
{
  cd "${LOG_DIRECTORY}";
  check_fail $? ${LINENO} "Can not enter directory ${LOG_DIRECTORY}" 7;
  local LATEST_FILE="$(ls -t | head -1)";
  local LAST_CHANGE=$(stat -c %Y $LATEST_FILE);
  local CURRENT_TIME=$(date +%s);
  local TIME_SINCE_CHANGE=$(( $CURRENT_TIME - $LAST_CHANGE ));
  local TIME_LIMIT=$(( 60*$TIME_LIMIT_MINUTES ));
  cd "${CURRENT_DIRECTORY}";

  if [[ ${TIME_SINCE_CHANGE} > ${TIME_LIMIT} ]];
  then
    do_warn "'${TOOLNAME}' did not change '${LATEST_FILE}' for more than ${TIME_LIMIT_MINUTES} minutes.";
    return 1;
  fi

  return 0;
}


status_loop ()
{
  for ((a=1; a <= $MAX_ITERATIONS ; a++))
  do
    do_log "Sleeping ${SLEEPING_TIME} seconds...";
    sleep ${SLEEPING_TIME};
    status && return 0; #break;
  done
  return 1;
}

start ()
{
  status && return 0;
  do_log "Starting ${TOOLNAME}....";

  #Checking if current user is application user. If current user is not application user you will be asked to exit.
  CURRENT_USER="$(whoami)";
  if [ "${CURRENT_USER}" != "${REQUIRED_USER}" ]
  then
    do_warn "Current user is not ${REQUIRED_USER}. Changing user.";
    sudo su - ${REQUIRED_USER} -c "${EXECUTION}";
    check_fail $? ${LINENO} "${TOOLNAME} could not be started." 3;
  else
    eval "${EXECUTION}";
    check_fail $? ${LINENO} "${TOOLNAME} could not be started." 4;
  fi

  status_loop
  check_fail $? ${LINENO} "${TOOLNAME} could not be started until now. Maybe more time is required." 5;
  return 0;
}

stop ()
{
  status || return 0;
  do_log "Stopping  ${TOOLNAME}....";
  [[ -n "${PID}" ]] && kill -9 "${PID}"
  sleep ${SLEEPING_TIME};
  status && do_warn "${TOOLNAME} has not been killed.";

  return 0;
}

restart ()
{
  stop
  do_log "Sleeping ${SLEEPING_TIME} seconds...";
  sleep ${SLEEPING_TIME};
  start
  return 0;
}


cd "${CURRENT_DIRECTORY}";
check_fail $? ${LINENO} "Can not enter directory ${CURRENT_DIRECTORY}" 1;

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}";
        exit 2;
esac

exit 0;


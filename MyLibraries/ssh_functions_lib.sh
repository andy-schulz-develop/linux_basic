#!/bin/bash

source "bash_libraries/bash_functions_lib.sh";
if [[ "$?" != "0" ]]; then
  echo "Source script not found";
  exit 1;
fi


TARGET_USER="rpm_deploy";
RPM_DEPLOY_ID_RSA_FILE="$( readlink -f ~/.ssh/id_rsa)"
KNOWN_HOSTS_FILE="$(readlink -f ~/.ssh/known_hosts)";
SCP_OPTIONS="-o IdentityFile=${RPM_DEPLOY_ID_RSA_FILE} -o UserKnownHostsFile=${KNOWN_HOSTS_FILE} -o StrictHostKeyChecking=no";
SSH_OPTIONS="-t -t -o IdentityFile=${RPM_DEPLOY_ID_RSA_FILE} -o UserKnownHostsFile=${KNOWN_HOSTS_FILE} -o StrictHostKeyChecking=no";


check_file "${RPM_DEPLOY_ID_RSA_FILE}" "${KNOWN_HOSTS_FILE}";
do_log "Adjusting permissions for ssh relevant files."
chmod 600 "${RPM_DEPLOY_ID_RSA_FILE}"
chmod 600 "${KNOWN_HOSTS_FILE}"

executeCommandOnServerViaRPM_DEPLOY()
{
  local USER="";
  local TARGET_USER="rpm_deploy";
  [[ -n "$1" ]] && COMMAND="$1";
  [[ -n "$2" ]] && TARGET_SERVER="$2";
  [[ -n "$3" ]] && ENVIRONMENT_NAME="$3";
  [[ -n "$4" ]] && USER="$4";
  do_log "Executing command: ${COMMAND}";
  if [[ -z "${USER}" ]]; then
    ssh ${SSH_OPTIONS} ${TARGET_USER}@${TARGET_SERVER} "${COMMAND}" 2> /dev/null
    check_warn $? ${LINENO} "SSH/Command failed. Command: ${COMMAND}" 7 || return 1;
  else
    ssh ${SSH_OPTIONS} ${TARGET_USER}@${TARGET_SERVER} "sudo su - ${USER} -c '${COMMAND}'" 2> /dev/null
    check_warn $? ${LINENO} "SSH/Command failed. Command: ${COMMAND}" 7 || return 1;
  fi
  return 0;
}

executeCommandOnServer()
{
  local USER="";
  [[ -n "$1" ]] && COMMAND="$1";
  [[ -n "$2" ]] && TARGET_SERVER="$2";
  [[ -n "$3" ]] && ENVIRONMENT_NAME="$3";
  [[ -n "$4" ]] && USER="$4";
  do_log "Executing command: ${COMMAND}";
  if [[ -z "${USER}" ]]; then
    ssh ${SSH_OPTIONS} ${TARGET_USER}@${TARGET_SERVER} "${COMMAND}" 2> /dev/null
    check_warn $? ${LINENO} "SSH/Command failed. Command: ${COMMAND}" 7;
  else
    ssh ${SSH_OPTIONS} ${USER}@${TARGET_SERVER} "${COMMAND}" 2> /dev/null
    check_warn $? ${LINENO} "SSH/Command failed. Command: ${COMMAND}" 7;
  fi
  return 0;
}



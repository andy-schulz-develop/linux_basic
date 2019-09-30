#!/bin/bash 

############################################################
##################### Global Variables #####################
############################################################

#COLORS
RED=`tput setaf 1`
GREEN=`tput setaf 2`
YELLOW=`tput setaf 3`
NC=`tput sgr0`
LANG="en_US.UTF-8";

CURRENT_SCRIPT="$(basename $0)";
CURRENT_SCRIPT="${CURRENT_SCRIPT%\.sh}"; #Cut the .sh away
CURRENT_SCRIPT="${CURRENT_SCRIPT#\.\/}"; #Cut ./ in the front away
CURRENT_DIRECTORY="$(dirname "$(readlink -f "$BASH_SOURCE")")";
CURRENT_SERVER="$(hostname -s | tr [:lower:] [:upper:])";
CURRENT_SERVER_FQDN="$(hostname --fqdn | tr [:lower:] [:upper:])";
TARGET_SERVER="${CURRENT_SERVER}";
ENVIRONMENT_NAME="Local";
NO_WARNINGS=0;
WARNINGS="";
LOGGING="false";
INDENTATION="";
TEMP_LINE="=========================================================";
SUMMARY="";
HEADER_FOR_SUMMARY="";


init()
{
#################################################
############## Specific Variables ###############
#################################################

  DEFAULT_MINIMUM_DISKSPACE=$((10 * 1024)); #Minimum diskspace in KB
  PACKAGE_NAME="...";
  INSTALLPATH="...";
  INSTALLATION_FOLDER="...";
  INSTALLATION_SOURCES_FOLDER="...";
  checkIfUpgrade "$*";
  enableLogging;
  return 0;
}

setParameters()
{
# This function enables setting parameters in the script call
#    Example: ./script.sh VARIABLE=content OTHERVAR="value"
# Does not support space separated lists (VARIABLE=content1 content2 content3)
  local EVAL_STRING="";
  [[ -z "$1" ]] && return 1;
  do_log "Parsing input";
  while [[ -n "$1" ]]; do
    # Sets --noscripts => noscripts="true"
    echo "$1" | grep -qE "^--\w+$"  && EVAL_STRING="${1#--}=\"true\"";
    # Sets VALUE => VALUE="true"
    echo "$1" | grep -qE "^\w+$"    && EVAL_STRING="$1=\"true\"";
    # Check if $1 is something like VARIABLE="value"
    echo "$1" | grep -qE "^\w+=.*$" && EVAL_STRING="$1";

    shift 1;
    [[ -z "${EVAL_STRING}" ]] && continue;
    do_log "Setting: '${EVAL_STRING}'" 2;
    eval "${EVAL_STRING}" 2>/dev/null
    check_warn $? ${LINENO} "Could not be set: '${EVAL_STRING}'";
    EVAL_STRING="";
  done
  return 0;
}

checkIfUpgrade()
{
  local SCRIPT_NAME="$(echo "${CURRENT_SCRIPT}" | tr [:upper:] [:lower:])";
  UPGRADE="no";
# Check if upgrade mode
  if [[ "${SCRIPT_NAME}" == *"prein"* || "${SCRIPT_NAME}" == *"postin"* ]]; then
    if [[(( "$#" > 0 )) && (( "$1" > 1 ))]]; then
      UPGRADE="yes"
      echo "This is an Upgrade.";
    fi
  fi

  if [[ "${SCRIPT_NAME}" == *"preun"* || "${SCRIPT_NAME}" == *"postun"* ]]; then
    if [[(( "$#" > 0 )) && (( "$1" > 0 ))]]; then
      UPGRADE="yes"
      echo "This is an Upgrade and ${CURRENT_SCRIPT} will not be executed."
      exit 0;
    fi
  fi
  return 0;
}

cleanup()
{
  do_log "Cleaning up";
  local ERRORCODE="${1:-0}";
  local TARGETS="";
  local TMP="";
  for object in ${TOBE_CLEANED}; do
    TMP="$(find $object -maxdepth 1 -type f 2>/dev/null)";
    [[ -n "${TMP}" ]] && TARGETS+="${TMP}"$'\n';
    TMP="$(find $object -maxdepth 1 -mindepth 1 -type d 2>/dev/null)";
    [[ -n "${TMP}" ]] && TARGETS+="${TMP}"$'\n';
  done
  [[ -z "${TARGETS}" ]] && return 0;

  if [[ "${ERRORCODE}" != "0" ]]; then
    echo "There are temporary files left. Have a look in:";
    echo "${TARGETS}"
  else
    echo "There are temporary files left. Removing them:";
    for object in ${TARGETS}; do
      rm -rv "${object}";
    done
  fi

  return 0;
}

exit_script()
{
  local TEMP_LINE="=========================================================";
  local ERRORCODE=$1;
  INDENTATION=0;
  cleanup;
  if [[ -n "${WARNINGS}" ]]; then
    echo "${TEMP_LINE}${TEMP_LINE}";
    echo "SHOWN WARNINGS:";
    echo "${WARNINGS}";
  fi
  echo "${TEMP_LINE}${TEMP_LINE}";
  if [[ "${ERRORCODE}" == "0" ]]; then
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SCRIPT COMPLETED";
  else
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SCRIPT FAILED";
  fi

  if [[ -n "${SUMMARY}" ]]; then
    echo "${TEMP_LINE}${TEMP_LINE}";
    HEADER_FOR_SUMMARY="${HEADER_FOR_SUMMARY}"$'\n';
    echo "${HEADER_FOR_SUMMARY}${SUMMARY}" | column -t
  fi

  echo "${TEMP_LINE}${TEMP_LINE}";
  exit ${ERRORCODE};
}

add()
{
  local VARIABLE_NAME="$1";
  local SUMMAND="$2";
  echo "${!VARIABLE_NAME}" | grep -qE ^-?[0-9]+$ || eval "${VARIABLE_NAME}=0"; # Checks if it is a number, if it is not sets VARIABLE to 0
  echo "${SUMMAND}" | grep -qE ^-?[0-9]+$ || SUMMAND=0; # Checks if it is a number, if it is not sets SUMMAND to 0
  eval "${VARIABLE_NAME}=$(( ${!VARIABLE_NAME} + ${SUMMAND} ))";
  return 0;
}

subtract()
{
  local MINUEND="$1";
  local SUBTRAHEND="$2";
  DIFFERENCE="";
  echo "${MINUEND}" | grep -qE ^-?[0-9]+$ || MINUEND=0; # Checks if it is a number
  echo "${SUBTRAHEND}" | grep -qE ^-?[0-9]+$ || SUBTRAHEND=0; # Checks if it is a number
  DIFFERENCE=$(( ${MINUEND} - ${SUBTRAHEND} ));
  return 0;
}

fail()
{
  local RETURNCODE="$1";
  local LINENUMBER="$2";
  local ERRORMESSAGE="$3";
  local ERRORCODE="1";
  [[ -n "$4" ]] && ERRORCODE="$4";
  local FUNCTION_OUTPUT="$5";
  local OUTPUT="ERROR: Command in line ${LINENUMBER} failed. Returncode: ${RETURNCODE}"$'\n';
  [[ -n "${FUNCTION_OUTPUT}" ]] && OUTPUT+="ERROR: Error message: ${FUNCTION_OUTPUT}"$'\n';
  OUTPUT+="ERROR: --Description: ${ERRORMESSAGE}";
  echo "${OUTPUT}" 1>&2;
  [[ "${LOGGING}" == "true" ]] && echo "${OUTPUT}";
  exit_script "${ERRORCODE}";
  exit "${ERRORCODE}";
  return 1;
}

check_fail()
{
  local RETURNCODE="$1";
  local LINENUMBER="$2";
  local ERRORMESSAGE="$3";
  local ERRORCODE="$4";
  local FUNCTION_OUTPUT="$5";
  if [[ "${RETURNCODE}" != "0" ]];  then
    fail "${RETURNCODE}" $((LINENUMBER-1)) "${ERRORMESSAGE}" "${ERRORCODE}" "${FUNCTION_OUTPUT}";
  fi
  #echo "Checkpoint No. ${ERRORCODE}";
  return 0;
}

do_log()
{
  local MESSAGE="$1";
  local LINE="";
  add "INDENTATION" "$2";
  if [[ (( $INDENTATION > 0 )) ]]; then
    LINE=" |";
    for ((i=1;i<=$INDENTATION;i++)); do LINE="${LINE}-"; done;
    add "INDENTATION" "-$2";
  else
    INDENTATION=0;
  fi
  echo "INFO $(date +%T) [${ENVIRONMENT_NAME}-${TARGET_SERVER}]: ${LINE} ${MESSAGE}"
  return 0;
}

warn()
{
  local RETURNCODE="$1";
  local LINENUMBER="$2";
  local ERRORMESSAGE="$3";
  local OUTPUT="WARNING: Command in line ${LINENUMBER} failed. Returncode: ${RETURNCODE}"$'\n';
  OUTPUT+="WARNING: Description: ${ERRORMESSAGE}";
  WARNINGS+=" |-- ${OUTPUT}"$'\n';
  add NO_WARNINGS 1;
  echo "${OUTPUT}" 1>&2;
  [[ "${LOGGING}" == "true" ]] && echo "${OUTPUT}";
  return 1;
}

check_warn()
{
  local RETURNCODE="$1";
  local LINENUMBER="$2";
  local ERRORMESSAGE="$3";
  if [[ ${RETURNCODE} != 0 ]]
  then
    warn "${RETURNCODE}" $((LINENUMBER-1)) "${ERRORMESSAGE}";
    return 1;
  fi
  return 0
}

addToSummary()
{
  local RETURN_VALUE="$1";
  local BASE_INFO="${MODE} $(basename "${RPM_FILE}") ${TARGET_SERVER}";
  [[ -z "${HEADER_FOR_SUMMARY}" ]] && HEADER_FOR_SUMMARY="= Mode Package Server Return Errors Warnings =";

  case "${RETURN_VALUE}" in
  "0")
    SUMMARY+="= ${BASE_INFO} Success ${NO_ERRORS:="?"} ${NO_WARNINGS:="?"} ="$'\n';
    return 0;
  ;;
  "1")
    SUMMARY+="= ${BASE_INFO} FAIL ${NO_ERRORS:="?"} ${NO_WARNINGS:="?"} ="$'\n';
    return 1;
  ;;
  "2")
    do_log "Skipping un/installation of ${RPM_FILE}";
    SUMMARY+="= ${MODE} $(basename "${package}") ${SERVER_LIST[$index]} Skipped - - ="$'\n';
    return 2;
  ;;
  *)
    SUMMARY+="= ${BASE_INFO} FAIL ${NO_ERRORS:="?"} ${NO_WARNINGS:="?"} ="$'\n';
    return 1;
  ;;
  esac
}

check_directory()
{
  do_log "Looking for required directory";
  [[ -z "$*" ]] && fail 1 ${LINENO} "Variables are empty" 2;
  add "INDENTATION" 2;
  for DIRECTORY in $*; do
    [[ -d "${DIRECTORY}" && -w "${DIRECTORY}" ]] || fail $? ${LINENO} "Directory '${DIRECTORY}' does not exist or is not writable." 2;
    do_log "Found: ${DIRECTORY}";
  done
  add "INDENTATION" -2;
  return 0;
}

check_file()
{
  do_log "Looking for required file(s)";
  [[ -z "$*" ]] && fail 1 ${LINENO} "Variables are empty" 2;
  add "INDENTATION" 2;
  for FILE in $*; do
    [[ -f "${FILE}" ]] || fail $? ${LINENO} "'${FILE}' can not be accessed." 3;
    do_log "Found: ${FILE}";
  done
  add "INDENTATION" -2;
  return 0;
}

check_if_set()
{
  local VARIABLE_NAME="$1";
  local DEFAULT_VALUE="$2";
  [[ -z "${VARIABLE_NAME}" ]] && fail 1 ${LINENO} "No variable name specified." 2;
  if [[ -z "${!VARIABLE_NAME}" ]]; then
    [[ -z "${DEFAULT_VALUE}" ]] && fail 1 ${LINENO} "Variable ${VARIABLE_NAME} is not set. No default value specified." 3;
    do_log "Variable ${VARIABLE_NAME} is not set. Setting to default: ${DEFAULT_VALUE}" 2;
    eval "${VARIABLE_NAME}=${DEFAULT_VALUE}";
    return 1;
  else
    return 0;
  fi
}

check_if_command_available()
{
  local COMMANDS="$*";
  for command in ${COMMANDS}; do
    do_log "Checking if command '${command}' is available";
    OUTPUT="$(which ${command} 2>&1)";
    check_fail $? ${LINENO} "Command '${command}' is not available. Make sure you are the right user on the right server." 4 "${OUTPUT}";
  done
  return 0;
}

enableLogging()
{
  local LOGFILE="$1";
  local LOGFOLDER="";
  check_if_set LOGFILE "/var/tmp/${PACKAGE_NAME}_${CURRENT_SCRIPT}_$(date +%s).log";
  LOGFOLDER="$(dirname "${LOGFILE}")";
  mkdir -p "${LOGFOLDER}";
  check_directory "${LOGFOLDER}";
  do_log "Output written to ${LOGFILE}";
  LOGGING="true";
#  exec > $out 2>&1
  exec > ${LOGFILE}
}

check_user()
{
  local USER="$1";
  local USERID="$2";
  local HOMEDIR="$3";
  local OUTPUT="";
  local CURRENT_USERID="";
  local CURRENT_HOME_DIR="";
  local RETURN_CODE="0";
  do_log "Checking if user exists: ${USER}";
  OUTPUT="$(id -u ${USER} 2>&1)";
  check_fail $? ${LINENO} "User does not exist: ${USER}" 4 "${OUTPUT}";
  CURRENT_USERID="$(id -u "${USER}" 2>/dev/null)";
  do_log "Found user: '${USER}', user id: '${USERID}'" 2;
## If USERID is set, checking if existing user has the right user id
  if [[ -n "${USERID}" && "${USERID}" != "${CURRENT_USERID}" ]]; then
    warn 1 ${LINENO} "User ID of user '${USER}' is '${CURRENT_USERID}' but should be '${USERID}'. Please check and recreate user" || RETURN_CODE="1";
  fi
## If HOMEDIR is set, checking if existing user has the right home directory
  if [[ -n "${HOMEDIR}" ]]; then
    CURRENT_HOME_DIR="$(readlink -f "$(cat /etc/passwd | grep -i "${USER}:" | cut -d: -f6)")";
    HOMEDIR="$(readlink -f "${HOMEDIR%\/}/")";
    [[ "${HOMEDIR%\/}/" == "${CURRENT_HOME_DIR%\/}/" ]];
    check_warn $? ${LINENO} "Home directory of user '${USER}' is '${CURRENT_HOME_DIR%\/}/' but should be '${HOMEDIR%\/}/'. Please check and recreate user" || RETURN_CODE="1";
  fi
  return ${RETURN_CODE};
}

checkFormat()
{
  local TARGET_FORMAT="$(echo "$1" | xargs | tr "[:lower:]" "[:upper:]")";
  local CURRENT_FORMAT="$(echo "$2" | xargs | tr "[:lower:]" "[:upper:]")";
  [[ "${CURRENT_FORMAT}" == "${TARGET_FORMAT}" ]] || fail $? ${LINENO} "The output format is not compatible. Expected format: '${TARGET_FORMAT}' vs. Current format: '${CURRENT_FORMAT}'";
  return 0;
}

check_diskspace()
{
  local TARGET_PATH="$1";
  local MINIMUM_DISKSPACE="$2";
  local FREE_DISKSPACE="";
  do_log "Checking free diskspace on '${TARGET_PATH}' ...";
  check_if_set "MINIMUM_DISKSPACE" "${DEFAULT_MINIMUM_DISKSPACE}";
  FREE_DISKSPACE="$(df -P ${TARGET_PATH} | tail -1 | awk '{print $4}')";
  check_warn $? ${LINENO} "Error occurred during calculation of diskspace.";
  if [[ ${FREE_DISKSPACE} -lt ${MINIMUM_DISKSPACE} ]]; then
    warn 1 ${LINENO} "Diskspace is low. Diskspace: ${FREE_DISKSPACE}KB Path: ${TARGET_PATH}";
    return 1;
  else
    do_log "OK. Diskspace: ${FREE_DISKSPACE}KB" 2;
    return 0;
  fi
}

check_server()
{
  local SERVER="$1";
  local PORT=$2;
  local PING_PACKAGES=1;
  local DEFAULT_PORT=22;
  local IP_ADDRESS;
  local RESULT;
  local TEMP="${TARGET_SERVER}";
  TARGET_SERVER="${SERVER}";  # Just for formatting reasons
  [[ -z "${PORT}" ]] && PORT=${DEFAULT_PORT}; # If no port specified, using default port

  do_log "Checking server: ${SERVER} port: ${PORT}";
  TARGET_SERVER="${TEMP}";  # Just for formatting reasons
  IP_ADDRESS="$(nslookup ${SERVER} | tail -4 | grep Address | awk '{print $2}')";
  if [[ "$?" != "0" ]]; then
    warn $? ${LINENO} "Could not get IP adress of server ${SERVER}";
    return 1;
  fi

  RESULT=$(bash -c 'exec 3<> /dev/tcp/'${IP_ADDRESS}'/'${PORT}';echo $?' 2>/dev/null)
  if [[ "${RESULT}" != "0" ]]; then
    warn 1 ${LINENO} "Connection to server ${SERVER} (IP:${IP_ADDRESS}) and port ${PORT} failed. Trying curl and ping"
    curl "http://${IP_ADDRESS}:${PORT}" 1>/dev/null 2>/dev/null;
    check_warn $? ${LINENO} "curl http://${IP_ADDRESS}:${PORT} failed.";
    ping -c ${PING_PACKAGES} "${SERVER}" 1>/dev/null 2>/dev/null;
    check_warn $? ${LINENO} "Ping to server ${SERVER} failed.";
    return 1;
  fi

  return 0;
}

waitForListener(){
  local SERVER="${1}"
  local PORT="${2}"
  check_if_set "SERVER";
  check_if_set "PORT";
  # the number of seconds to sleep between the checks
  local sleepInSeconds=5
  { < /dev/tcp/${SERVER}/${PORT}; } 2>/dev/null
  while [[ "$?" != "0" ]]; do
    do_log "Waiting for the listener to start on ${SERVER}:${PORT}. Sleeping for ${sleepInSeconds} seconds" 2;
    sleep ${sleepInSeconds}
    { < /dev/tcp/${SERVER}/${PORT}; } 2>/dev/null
  done
  do_log "Listener up and running"
  sleep ${sleepInSeconds}
  return 0;
}

waitForServerUntilTimeout(){
  local SERVER=${1}
  local PORT=${2}
  local TIMEOUT_SECONDS=${3}

  export TARGET_SERVER ENVIRONMENT_NAME TOBE_CLEANED WARNINGS LOGGING INDENTATION
  export -f add do_log check_if_set fail exit_script cleanup waitForListener
  timeout ${TIMEOUT_SECONDS} bash -c "waitForListener ${SERVER} ${PORT}";
  check_fail $? ${LINENO} "Listener didn't come up during the maximum waiting duration of ${TIMEOUT_SECONDS} seconds" 8
  return 0;
}

printParameters()
{
  local VARIABLES="$*";
  local OUTPUT="";
  local PREFIX="";
  PREFIX="$(do_log "" 2)";

  for VARIABLE in ${VARIABLES}; do
    check_if_set "${VARIABLE}";
    OUTPUT+="$(echo "${PREFIX}${VARIABLE}:?${!VARIABLE}")"$'\n';
  done
  echo "${OUTPUT}" | column -s'?' -t;
  return 0;
}

removeStringIfContained()
{
  local VARIABLE_NAME="$1";
  local TO_BE_REMOVED="$2";
  local VARIABLE_CONTENT="${!VARIABLE_NAME}";
  if [[ "${VARIABLE_CONTENT}" == *"${TO_BE_REMOVED}"* ]]; then
    VARIABLE_CONTENT="${VARIABLE_CONTENT/${TO_BE_REMOVED}}";
    eval "${VARIABLE_NAME}=\"${VARIABLE_CONTENT}\""
    return 0;
  else
    return 1;
  fi
}

create_group()
{
  local GROUP="$1";
  local GROUPID="$2";
  local OUTPUT="";
  do_log "Checking if group exists: ${GROUP}";
  #id -g "${GROUP}" 1>/dev/null 2>/dev/null
  getent group ${GROUP} 2>&1 1>/dev/null;
  if [[ $? != 0 ]];
  then
    # Creating group
    do_log "Creating group: ${GROUP}, GroupID: ${GROUPID}";
    OUTPUT="$(groupadd --gid "${GROUPID}" "${GROUP}" 2>&1)";
    check_fail $? ${LINENO} "Creation of group failed: ${GROUP}" 2 "${OUTPUT}";
  else
    do_log "Group ${GROUP} already exists.";
  fi
  return 0;
}

create_user()
{
  local USER="$1";
  local USERID="$2";
  local HOMEDIR="$3";
  local GROUP="$4";
  local USER_CREATION_COMMAND="sudo useradd -s /bin/bash";
  ### For password encryption
  local ALGORITHM="1"; ##MD5-based password algorithm
  local PASSWORD_SALT="";
  [[ -z "${SALT}" ]] && PASSWORD_SALT="sdfklsdf";
  check_if_set "USER";

  do_log "Checking if user exists: ${USER}";
  id -u ${USER} 1>/dev/null 2>/dev/null
  if [[ "$?" == "0" ]]; then
    do_log "User does already exist.";
    if [[ -n "${HOMEDIR}" ]]; then
      local CURRENTHOME="$(readlink -f "$(cat /etc/passwd | grep "${USER}:" | cut -d: -f6)")";
      HOMEDIR="$(readlink -f "${HOMEDIR%\/}/")";
      if [[ "${CURRENTHOME%/}" != "${HOMEDIR%/}" ]]; then
        check_warn 1 ${LINENO} "Current home directory is '${CURRENTHOME%/}' but should be '${HOMEDIR%/}'. Please remove/backup and reinstall this package.";
        #usermod --home "${HOMEDIR}" -m "${USER}" 2>&1
        #check_warn $? ${LINENO} "Moving the home directory from '${CURRENTHOME%/}' to '${HOMEDIR%/}' failed.";
      fi
    fi
    return 1;
  fi

  if [[ -n "${USERID}" ]]; then
    USER_CREATION_COMMAND+=" --uid ${USERID}";
  fi

  do_log "Checking for running processes for user '${USER}'";
  ps -fU "${USERID:-${USER}}" 2>&1 1>/dev/null  # If USERID is empty looking for USER name
  if [[ "$?" == "0" ]]; then
    ps -fU "${USERID:-${USER}}"; 
    fail 1 ${LINENO} "There are running processes for user '${USERID:-${USER}}'. See list above. Please check and kill them."
  fi

  if [[ -n "${HOMEDIR}" ]]; then
    USER_CREATION_COMMAND+=" -m --home-dir ${HOMEDIR}";
    [[ -e "${HOMEDIR}" ]] && fail 1 ${LINENO} "Folder '${HOMEDIR}' already exists. Please remove/backup and reinstall this package.";
    mkdir -p "$(dirname "${HOMEDIR}")";
    check_fail $? ${LINENO} "Not able to create folder '$(dirname "${HOMEDIR}")'" 3;
  fi

  if [[ -n "${GROUP}" ]]; then
    USER_CREATION_COMMAND+=" -g ${GROUP}";
    create_group "${GROUP}" "${USERID}";
  fi

  do_log "Creating user '${USER}', UserID: '${USERID}', Group: '${GROUP}', Home directory: '${HOMEDIR}'";
  if [[ -n "${DEFAULT_PASSWORD}" ]]; then
    do_log "Setting default password '${DEFAULT_PASSWORD}'. Please change immediately!" 2;
    USER_CREATION_COMMAND+=" --password $(openssl passwd "-${ALGORITHM}" -salt "${PASSWORD_SALT}" "${DEFAULT_PASSWORD}")";
    eval "${USER_CREATION_COMMAND} ${USER}" 2>&1
    check_fail $? ${LINENO} "Creation of user failed: ${USER}" 1;
    sudo chage -d 0 "${USER}";
    check_warn $? ${LINENO} "Enforcing password renewal failed";
  else
    eval "${USER_CREATION_COMMAND} ${USER}" 2>&1
    check_fail $? ${LINENO} "Creation of user failed: ${USER}" 1;
  fi

  return 0;
}

remove_user()
{
  local USER="$1";
  local USERID="$2";
  do_log "Checking if user exists: ${USER}";
  USERID="$(id -u ${USER} 2>/dev/null)";
  if [[ $? == 0 ]];
  then
    do_log "Removing user ${USER}";
    userdel -f ${USER};
    check_warn $? ${LINENO} "User ${USER} could not be removed.";
  else
    do_log "User ${USER} does not exist.";
  fi

  do_log "Removing mail directory, if exists.";
  delete_function "/var/spool/mail/${USER}";

  if [[ -n "${USERID}" ]]; then
    do_log "Checking for running processes for user '${USER}' (UserID: '${USERID}')";
    ps -fU "${USERID}" 2>&1 1>/dev/null
    if [[ "$?" == "0" ]]; then
      ps -fU "${USERID}"; 
      warn 1 ${LINENO} "There are running processes for UserID '${USERID}'. See list above. Please check and kill them."
    fi
  fi
  return 0;
}

remove_group()
{
  local GROUP="$1";
  do_log "Checking if group ${GROUP} exists.";
  id -g "${GROUP}" 1>/dev/null 2>/dev/null
  if [[ $? == 0 ]];
  then
    do_log "Removing group ${GROUP}";
    groupdel "${GROUP}";
    check_warn $? ${LINENO} "Group ${GROUP} could not be removed.";
  else
    do_log "Group ${GROUP} does not exist.";
  fi

  return 0;
}

copy_function()
{
  local SOURCE="$1";
  local TARGET="$2";
  local TARGET_DIR="";
  local OUTPUT="";
  do_log "Copying '${SOURCE}'" 2;
  do_log "to '${TARGET}'" 7;
  if [[ -e "${SOURCE}" ]]; then
    if [[ "${TARGET}" == *"/" ]]; then
      TARGET_DIR="${TARGET}";
    else
      TARGET_DIR="$(dirname "${TARGET}")";
    fi
    OUTPUT="$(mkdir -p "${TARGET_DIR}" 2>&1)";
    check_fail $? ${LINENO} "Target directory is not accessible: ${TARGET_DIR}" 4 "${OUTPUT}";
    OUTPUT="$(cp -a ${SOURCE} ${TARGET} 2>&1)";
    check_fail $? ${LINENO} "Copy command failed: cp -a ${DIRECTORY} ${TARGET}" 4 "${OUTPUT}";
  else
    fail $? ${LINENO} "${SOURCE} can not be accessed." 4;
  fi
  do_log "Success" 2;
  return 0;
}

delete_function()
{
  local TARGET="";
  for TARGET in $*; do
    if [[ -L "${TARGET}" || -e "${TARGET}" ]]; then
      do_log "Deleting '${TARGET}'" 4;
      rm -rf "${TARGET}";
      check_warn $? ${LINENO} "Remove command failed: rm -rf ${TARGET}" || continue;
    else
      do_log "'${TARGET}' is probably already removed or can not be accessed." 6;
    fi
  done
  return 0;
}

remove_content_from_file()
{
  local TARGET_FILE="$1";
  local INSERT_TAG_BEGIN="$2";
  local INSERT_TAG_END="$3";

  if [[ ! -f "${TARGET_FILE}" ]]; then
    warn 1 ${LINENO} "File does not exist. File: ${TARGET_FILE}";
    return 1;
  fi

  grep -q -e "${INSERT_TAG_BEGIN}" -e "${INSERT_TAG_END}" "${TARGET_FILE}";
  if [[ $? == 0 ]]; then
    do_log "Removing previously appended content.";
    sed -i "/${INSERT_TAG_BEGIN}/,/${INSERT_TAG_END}/d" "${TARGET_FILE}";
    check_warn $? ${LINENO} "Old content could not be removed. Please check file: ${TARGET_FILE}";
  fi
  return 0;
}

searchAndReplaceInFile()
{
  local TOBE_REPLACED="$1";
  local REPLACEMENT="$2";
  local FILE="$3";
  local INSERT_TAG_BEGIN="$4";
  local INSERT_TAG_END="$5";
  local INSERT_TAG="true";

  [[ -z "${INSERT_TAG_BEGIN}" ]] && INSERT_TAG="false";
  [[ -z "${INSERT_TAG_END}" ]] && INSERT_TAG="false";

  do_log "Searching and replacing in '${FILE}'";
  add "INDENTATION" 2;
  check_file "${FILE}";
  add "INDENTATION" -2;

  if [[ "${INSERT_TAG}" == "true" ]]; then
    remove_content_from_file "${FILE}" "${INSERT_TAG_BEGIN}" "${INSERT_TAG_END}";
    REPLACEMENT="${INSERT_TAG_BEGIN}\n${REPLACEMENT}\n${INSERT_TAG_END}";
  fi

  do_log "Searching for:" 2;
  do_log "${TOBE_REPLACED}" 4;
  do_log "Replacing with:" 2;
  do_log "${REPLACEMENT}" 4;
  
  # Removing trailing blank lines from destination file
  #sed --in-place -e :a -e '/^\n*$/{$d;N;};/\n$/ba' "${DESTINATION_FILE}"
  grep -q "${TOBE_REPLACED}" "${FILE}";
  if [[ "$?" == "0" ]]; then
    # Actual replacing
    sed -i -e "s|${TOBE_REPLACED}|${REPLACEMENT}|" ${FILE};
    check_fail $? ${LINENO} "Replacement in '${FILE}' failed." 4;
  else
    do_log "Search string not found. Skipping replacement.";
    return 1;
  fi

  # Adding a blank line to the end of the target file
  #cat "${DESTINATION_FILE}" | tail -1 | grep -q "^$" || echo >> "${DESTINATION_FILE}"
  return 0;
}

appendFileContentToFile()
{
  local SOURCE_FILE="$1";
  local DESTINATION_FILE="$2";
  local INSERT_TAG_BEGIN="$3";
  local INSERT_TAG_END="$4";
  local INSERT_TAG="true";
  local OUTPUT="";

  [[ -z "${INSERT_TAG_BEGIN}" ]] && INSERT_TAG="false";
  [[ -z "${INSERT_TAG_END}" ]] && INSERT_TAG="false";

  do_log "Appending file content from file '${SOURCE_FILE}'";
  do_log "to '${DESTINATION_FILE}'" 30;
  check_file "${SOURCE_FILE}";

  # If DESTINATION_FILE exists removing old tags else recreating DESTINATION_FILE
  if [[ -f "${DESTINATION_FILE}" ]]; then
    [[ "${INSERT_TAG}" == "true" ]] && remove_content_from_file "${DESTINATION_FILE}" "${INSERT_TAG_BEGIN}" "${INSERT_TAG_END}"
  else
    OUTPUT="$(mkdir -p "$(dirname ${DESTINATION_FILE})" 2>&1)";
    check_fail $? ${LINENO} "Directory is not accessible: $(dirname ${DESTINATION_FILE})" 4 "${OUTPUT}";
    OUTPUT="$(touch ${DESTINATION_FILE} 2>&1)";
    check_fail $? ${LINENO} "File cannot be created: ${DESTINATION_FILE}" 4 "${OUTPUT}";
  fi

  # Removing trailing blank lines from destination file
  sed --in-place -e :a -e '/^\n*$/{$d;N;};/\n$/ba' "${DESTINATION_FILE}"

  # Actual appending
  if [[ "${INSERT_TAG}" == "true" ]]; then
    do_log "Inserting tags ${INSERT_TAG_BEGIN} ... ${INSERT_TAG_END}" 2;
    echo -e "${INSERT_TAG_BEGIN}\n" >> "${DESTINATION_FILE}";
    cat "${SOURCE_FILE}" >> "${DESTINATION_FILE}";
    check_fail $? ${LINENO} "Appending file content from '${SOURCE_FILE}' to '${DESTINATION_FILE}' failed." 4;
    echo -e "${INSERT_TAG_END}\n" >> "${DESTINATION_FILE}";
  else
    do_log "Inserting data without tags" 2;
#    cat "${SOURCE_FILE}" >> "${DESTINATION_FILE}";
    eval "echo \"$(cat ${SOURCE_FILE})\"" >> "${DESTINATION_FILE}";
    check_fail $? ${LINENO} "Appending file content from '${SOURCE_FILE}' to '${DESTINATION_FILE}' failed." 4;
  fi

  # Adding a blank line to the end of the target file
  cat "${DESTINATION_FILE}" | tail -1 | grep -q "^$" || echo >> "${DESTINATION_FILE}"
  return 0;
}

appendScriptOuputToFile()
{
  local SOURCE_FILE="$1";
  local DESTINATION_FILE="$2";
  local INSERT_TAG_BEGIN="$3";
  local INSERT_TAG_END="$4";
  local INSERT_TAG="true";
  local OUTPUT="";

  [[ -z "${INSERT_TAG_BEGIN}" ]] && INSERT_TAG="false";
  [[ -z "${INSERT_TAG_END}" ]] && INSERT_TAG="false";

  do_log "Appending script output from '${SOURCE_FILE}'";
  do_log "to '${DESTINATION_FILE}'" 30;
  check_file "${SOURCE_FILE}";

  # If DESTINATION_FILE exists removing old tags else recreating DESTINATION_FILE
  if [[ -f "${DESTINATION_FILE}" ]]; then
    [[ "${INSERT_TAG}" == "true" ]] && remove_content_from_file "${DESTINATION_FILE}" "${INSERT_TAG_BEGIN}" "${INSERT_TAG_END}"
  else
    OUTPUT="$(mkdir -p "$(dirname ${DESTINATION_FILE})" 2>&1)";
    check_fail $? ${LINENO} "Directory is not accessible: $(dirname ${DESTINATION_FILE})" 4 "${OUTPUT}";
    OUTPUT="$(touch ${DESTINATION_FILE} 2>&1)";
    check_fail $? ${LINENO} "File cannot be created: ${DESTINATION_FILE}" 4 "${OUTPUT}";
  fi

  # Removing trailing blank lines from destination file
  sed --in-place -e :a -e '/^\n*$/{$d;N;};/\n$/ba' "${DESTINATION_FILE}"

  # Actual appending
  if [[ "${INSERT_TAG}" == "true" ]]; then
    do_log "Inserting tags ${INSERT_TAG_BEGIN} ... ${INSERT_TAG_END}" 2;
    echo -e "${INSERT_TAG_BEGIN}\n" >> "${DESTINATION_FILE}";
    source "${SOURCE_FILE}" >> "${DESTINATION_FILE}";
    check_fail $? ${LINENO} "Appending script output from '${SOURCE_FILE}' to '${DESTINATION_FILE}' failed." 4;
    echo -e "${INSERT_TAG_END}\n" >> "${DESTINATION_FILE}";
  else
    do_log "Inserting data without tags" 2;
    source "${SOURCE_FILE}" >> "${DESTINATION_FILE}";
    check_fail $? ${LINENO} "Appending script output from '${SOURCE_FILE}' to '${DESTINATION_FILE}' failed." 4;
  fi

  # Adding a blank line to the end of the target file
  cat "${DESTINATION_FILE}" | tail -1 | grep -q "^$" || echo >> "${DESTINATION_FILE}"
  return 0;
}

appendTextToFile()
{
#SOURCE_FILE="${INSTALLPATH}${INSTALLATION_SOURCES_FOLDER}etc/system/local/${PACKAGE_NAME}_authorize.conf";
#DESTINATION_FILE="${INSTALLPATH}${INSTALLATION_FOLDER}etc/system/local/authorize.conf";
#INSERT_TAG_BEGIN="###${PACKAGE_NAME}_INSERTION - BEGIN";
#INSERT_TAG_END="###${PACKAGE_NAME}_INSERTION - END";
#append_to_file "${SOURCE_FILE}" "${DESTINATION_FILE}" "${INSERT_TAG_BEGIN}" "${INSERT_TAG_END}";

  local TEXT="$1";
  local DESTINATION_FILE="$2";
  local INSERT_TAG_BEGIN="$3";
  local INSERT_TAG_END="$4";
  local INSERT_TAG="true";
  local OUTPUT="";

  [[ -z "${INSERT_TAG_BEGIN}" ]] && INSERT_TAG="false";
  [[ -z "${INSERT_TAG_END}" ]] && INSERT_TAG="false";
  check_if_set "TEXT";

  do_log "Appending to file '${DESTINATION_FILE}'";

  # If DESTINATION_FILE exists removing old tags else recreating DESTINATION_FILE
  if [[ -f "${DESTINATION_FILE}" ]]; then
    [[ "${INSERT_TAG}" == "true" ]] && remove_content_from_file "${DESTINATION_FILE}" "${INSERT_TAG_BEGIN}" "${INSERT_TAG_END}"
  else
    OUTPUT="$(mkdir -p "$(dirname ${DESTINATION_FILE})" 2>&1)";
    check_fail $? ${LINENO} "Directory is not accessible: $(dirname ${DESTINATION_FILE})" 4 "${OUTPUT}";
    OUTPUT="$(touch ${DESTINATION_FILE} 2>&1)";
    check_fail $? ${LINENO} "File cannot be created: ${DESTINATION_FILE}" 4 "${OUTPUT}";
  fi

  # Removing trailing blank lines from destination file
  sed --in-place -e :a -e '/^\n*$/{$d;N;};/\n$/ba' "${DESTINATION_FILE}"

  # Actual appending
  if [[ "${INSERT_TAG}" == "true" ]]; then
    do_log "Inserting tags ${INSERT_TAG_BEGIN} ... ${INSERT_TAG_END}" 2;
    echo -e "${INSERT_TAG_BEGIN}\n" >> "${DESTINATION_FILE}";
    echo "${TEXT}" >> "${DESTINATION_FILE}";
    check_fail $? ${LINENO} "Appending to file '${DESTINATION_FILE}' failed." 4;
    echo -e "${INSERT_TAG_END}\n" >> "${DESTINATION_FILE}";
  else
    do_log "Inserting data without tags" 2;
    echo "${TEXT}" >> "${DESTINATION_FILE}";
    check_fail $? ${LINENO} "Appending to file '${DESTINATION_FILE}' failed." 4;
  fi

  # Adding a blank line to the end of the target file
  cat "${DESTINATION_FILE}" | tail -1 | grep -q "^$" || echo >> "${DESTINATION_FILE}"
  return 0;
}

recreate_folder()
{
  local TARGET="${1%\/}";
  local OUTPUT="";
  do_log "(Re-)Creating folder '${TARGET}'" 2;

  if [[ -L "${TARGET}" ]]; then
    do_log "There is a symbolic link named like the target folder, removing it." 4;
    delete_function "${TARGET}";
  fi

  if [[ -f "${TARGET}" ]]; then
    local NEW_FILENAME="${TARGET}_backup";
    do_log "There is already a file. Moving it to ${NEW_FILENAME}" 4;
    OUTPUT="$(mv "${TARGET}" "${NEW_FILENAME}" 2>&1)";
    check_fail $? ${LINENO} "Moving failed!" 7 "${OUTPUT}";
  fi

  if [[ -d "${TARGET}" ]]; then
    do_log "Folder already exists" 2;
    check_if_empty "${TARGET}"
    return 0;
  fi

  OUTPUT="$(mkdir -p ${TARGET} 2>&1)";
  check_fail $? ${LINENO} "Folder is missing and could not be created (${TARGET})" 9 "${OUTPUT}";
  do_log "Folder created successfully" 2;
  return 0;
}

recreate_link()
{
  local LINKFILE="${1%\/}";
  local TARGET="${2%\/}";
  local OUTPUT="";
  do_log "(Re-)Creating link ${LINKFILE}";
  do_log "-> ${TARGET}" 14;
  [[ -e "${TARGET}" ]] || fail $? ${LINENO} "Target does not exist: ${TARGET}";

  if [[ -L "${LINKFILE}" ]]; then
     if [[ -e "${LINKFILE}" ]]; then
       local EXISTING_TARGET="$(readlink "${LINKFILE}")";
       do_log "A link does already exist: ${LINKFILE} -> ${EXISTING_TARGET}" 2;
       [[ "${TARGET}" == "${EXISTING_TARGET}" ]] && return 0;
     else
        do_log "A link does already exist, but is broken." 2;
     fi
     delete_function "${LINKFILE}";
  elif [ -e ${LINKFILE} ] ; then
     local NEW_FILENAME="${LINKFILE}_backup";
     do_log "There is already a file/directory. Moving it to ${NEW_FILENAME} 2";
     OUTPUT="$(mv "${LINKFILE}" "${NEW_FILENAME}" 2>&1)";
     check_fail $? ${LINENO} "Moving failed!" 7 "${OUTPUT}";
  fi

  OUTPUT="$(ln -s ${TARGET} ${LINKFILE} 2>&1)";
  check_fail $? ${LINENO} "Logic link is missing and could not be created (${LINKFILE} -> ${TARGET})" 9 "${OUTPUT}";
  add "INDENTATION" -2;
  do_log "Link created successfully";
  return 0;
}

check_if_empty()
{
  local DIRECTORY="$1";
  local RESULT="";
  RESULT="$(find "${DIRECTORY}" -maxdepth 0 -type d -empty 2>/dev/null)";
  if [[ "$?" != "0" ]]; then
    warn 1 ${LINENO} "Could not find ${DIRECTORY}.";
    return 2;
  fi
  if [[ -d "${RESULT}" ]]; then
    do_log "Directory ${DIRECTORY} is empty." 2;
    return 0;
  else
    do_log "Directory ${DIRECTORY} seems not empty." 2;
    return 1;
  fi
}



################# INTERACTIVE FUNCTIONS ##################################
## Can not be used in RPMs

ask()
{
  local QUESTION="$1";
  local DEFAULT_ANSWER="$2";
  local QUESTION_TIMEOUT="$3";
  local CONFIRMATION="";

  if [[ -n "${DEFAULT_ANSWER}" ]]; then
    QUESTION="${QUESTION}(Default: ${DEFAULT_ANSWER})";
  else
    fail $? ${LINENO} "Variable DEFAULT_ANSWER is empty." 7;
  fi

  echo "${QUESTION_TIMEOUT}" | grep -qE ^[0-9]+$ # Checks if timeout is a number
  if [[ "$?" != "0" ]]; then
    read -p "${QUESTION} " CONFIRMATION
  else
    read -t "${QUESTION_TIMEOUT}" -p "${QUESTION} " CONFIRMATION
  fi
  echo

  CONFIRMATION="$(echo "${CONFIRMATION}" | tr "[:lower:]" "[:upper:]")";
  DEFAULT_ANSWER="$(echo "${DEFAULT_ANSWER}" | tr "[:lower:]" "[:upper:]")";
  if [[ "${CONFIRMATION:="${DEFAULT_ANSWER}"}" == "${DEFAULT_ANSWER}" ]]; then
    return 0;
  else
    return 1;
  fi
}

askForInfo()
{
  local QUESTION="$1";
  local DEFAULT_ANSWER="$2";
  local QUESTION_TIMEOUT="$3";
  INPUT="";
  [[ -n "${DEFAULT_ANSWER}" ]] && QUESTION="${QUESTION}(Default: ${DEFAULT_ANSWER})";
  echo "${QUESTION_TIMEOUT}" | grep -qE ^[0-9]+$ # Checks if timeout is a number
  if [[ "$?" != "0" ]]; then
    read -r -p "${QUESTION} " INPUT
  else
    read -r -t "${QUESTION_TIMEOUT}" -p "${QUESTION} " INPUT
  fi
  [[ -z "${INPUT}" ]] && INPUT="${DEFAULT_ANSWER}";
  return 0;
}

askForPassword()
{
  local QUESTION="$1";
  PASSWORD="";
  read -s -p "${QUESTION} " PASSWORD
  echo;
  return 0;
}

askForInfoAndCheckAnswer()
{
  local DOCUMENTATION="
This function needs two parameters.
The first parameter contains the question as string.
The second parameter contains the name of a function that checks the user input. That function has to fulfill some requirements:
- It has to accept exactly one string parameter.
- If the check is positive the return code has to be 0, if not the return code has to be something else.
- It is recommended to suppress the output of this function.";

  local QUESTION="$1";
  local CHECK_FUNCTION="$2";
  local DEFAULT_ANSWER="$3";
  local QUESTION_TIMEOUT="$4";
  INPUT="";

  check_if_set "CHECK_FUNCTION" "checkAnswer";

  askForInfo "${QUESTION}" "${DEFAULT_ANSWER}" "${QUESTION_TIMEOUT}";
  eval "${CHECK_FUNCTION} ${INPUT}";
  while [[ "$?" != "0"  ]]; do
    askForInfo "${QUESTION}" "${DEFAULT_ANSWER}" "${QUESTION_TIMEOUT}";
    eval "${CHECK_FUNCTION} ${INPUT}";
  done;

  return 0;
}





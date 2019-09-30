#!/bin/bash

source "bash_libraries/bash_functions_lib.sh";
if [[ "$?" != "0" ]]; then
  echo "Source script not found";
  exit 1;
fi

OUTPUT="$(which svn 2>&1)";
check_fail $? ${LINENO} "SVN command not found. Please install 'subversion' and restart script." 4 "${OUTPUT}";

getSVNCredentials()
{
  local SVN_SOURCE_PATH="$1";
  local SVN_USER="";
  local PASSWORD="";
# Getting correct SVN password
# First trying without password then searching for correct one
  svn log --limit 1 --non-interactive "${SVN_SOURCE_PATH}" 1>/dev/null 2>/dev/null;
  if [[ "$?" != "0"  ]]; then
    svn log --limit 1 ${CREDENTIALS_STRING} --non-interactive "${SVN_SOURCE_PATH}" 1>/dev/null 2>/dev/null;
    while [[ "$?" != "0"  ]]; do
      do_log "Username/Password seems to be empty or not correct.";
      askForInfo "Please enter username for SVN access:" "${SVN_USER}";
      SVN_USER="${INPUT}";
      askForPassword "Please enter password for SVN access:";
      CREDENTIALS_STRING="--username ${SVN_USER} --password ${PASSWORD}"
      svn log --limit 1 ${CREDENTIALS_STRING} --non-interactive "${SVN_SOURCE_PATH}" 1>/dev/null 2>/dev/null;
    done;
  else
    do_log "SVN password seems to be already saved locally.";
  fi
  PASSWORD="";

  return 0;
}


updateOrCheckout()
{
  local SVN_SOURCE_PATH="$1";
  local TARGET_DIRECTORY="$2";
  check_if_set "SVN_SOURCE_PATH";
  check_if_set "TARGET_DIRECTORY";

  getSVNCredentials "${SVN_SOURCE_PATH}";

# Checking out/ Updating
  svn info "${TARGET_DIRECTORY}" 1>/dev/null 2>/dev/null;
  if [[ "$?" == "0" ]]; then
    do_log "Updating '${TARGET_DIRECTORY}'";
    svn update ${CREDENTIALS_STRING} --non-interactive "${TARGET_DIRECTORY}";
    check_fail $? ${LINENO} "Was not able to update '${TARGET_DIRECTORY}'" 4;
  else
    delete_function "${TARGET_DIRECTORY}";
    do_log "Checking out '${TARGET_DIRECTORY}'";
    svn checkout ${CREDENTIALS_STRING} --non-interactive "${SVN_SOURCE_PATH}" "${TARGET_DIRECTORY}";
    check_fail $? ${LINENO} "Was not able to checkout '${TARGET_DIRECTORY}'" 4;
  fi

  return 0;
}

commit()
{
  local DIRECTORY="$1";
  local OUTPUT="";
  local SVN_PATH="";
  # Enter target folder
  cd "${DIRECTORY}";
  OUTPUT="$(svn info 2>&1)";
  check_fail $? ${LINENO} "Folder '${DIRECTORY}' was not checked out properly" 4 "${OUTPUT}";
  do_log "Adding unknown files if necessary" 2;
  svn status | grep "^?" | cut -d? -f2- | xargs --no-run-if-empty svn add;
  # Getting SVN link for credentials
  SVN_PATH="$(svn info | grep -i "url:" | cut -d: -f2 | xargs)";
  getSVNCredentials "${SVN_PATH}";
  do_log "Committing modified and added files";
  svn commit -m "[MQSuite] Generated new files";
  # Return to previous folder
  cd -;

  return 0;
}

svn_export()
{
  local SVN_SOURCE_PATH="$1";
  local TARGET_DIRECTORY="$2";
  check_if_set "SVN_SOURCE_PATH";
  check_if_set "TARGET_DIRECTORY";

  do_log "Exporting files from SVN path '${SVN_SOURCE_PATH}'" 2;
  do_log "-------------------------- to '${TARGET_DIRECTORY}'" 2;

  getSVNCredentials "${SVN_SOURCE_PATH}";

  svn export ${CREDENTIALS_STRING} --non-interactive "${SVN_SOURCE_PATH}" "${TARGET_DIRECTORY}";
  check_fail $? ${LINENO} "Exporting files to target path '${TARGET_DIRECTORY}' failed! Please check diskspace and permissions." 4;

  return 0;
}



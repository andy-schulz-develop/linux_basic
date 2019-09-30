#!/bin/bash

set -vx

# $* contains all input parameters as string
echo $*

# $1 contains first input parameter (separator is space)
echo $1

# $2 contains second input parameter (separator is space)
echo $2

# $# contains number of input parameters
echo $#

# $? contains return value of previous command. 0 is success. Any other value represents failure (VERY IMPORTANT)
echo $?

# $LINENO is current linenumber. 20 in this case
echo $LINENO

# $BASH_SOURCE contains the call of the script. Useful for determining where the current script is: readlink -e ${BASH_SOURCE}
echo $BASH_SOURCE

echo "######################################";
read

# Quotation marks are very important!!!!
# When they are not used, bash may split one string into several ones.
VARIABLE="content";
FiLE_PatH="./THIS is a folder/";

# mkdir creates folders. See manual for more information
mkdir -vp ${FiLE_PatH};
mkdir -vp "${FiLE_PatH}";

rm -rvf "${FiLE_PatH}";
#rm -rvf ${FiLE_PatH};
rm -rvf "./THIS";


echo "######################################";
read

# % removes characters from the end of a string. Very handy to prevent double / in file paths
echo "${FiLE_PatH%/}/";

# # removes characters from the beginning of a string. If there is no such character nothing happens
echo "${FiLE_PatH#/}";

# # removes characters from the beginning of a string
echo "${FiLE_PatH#.}";

# Cuts out 2 characters starting from the third character
echo "${FiLE_PatH:3:2}";

# ^^ changes letters to upper case
echo "${FiLE_PatH^^}";

# ,, changes letters to lower case
echo "${FiLE_PatH,,}";

echo "######################################";
read

# Syntax of for loop:
for letter in a b c d e f; do
  echo "${letter}";
done

# In this case quotation marks may lead to unwanted behaviour
for letter in "a b c d e f"; do
  echo "${letter}";
done

echo "######################################";
read

# Writing output into variable
INPUT="$(find . -name templateInstallScript.sh)";
echo "${INPUT}";

# Only standard output (1) is written into variable. Errors won't be written into INPUT since they just occur on standard error output (2)
INPUT="$(find wurst)";
echo "${INPUT}";

# Outputs can be redirected. 2>&1 redirects from standard error to standard out (1)
INPUT="$(find wurst 2>&1)";
echo "${INPUT}";

# /dev/null is the void. Output will be trashed
find wurst 2>/dev/null

echo "######################################";
read

# Syntax of if statement
if [[ "AB" == "AB" ]]; then
  echo "AB is AB";
fi

# Calculating is a pain in bash
if [[ (( 1 < 2 )) ]]; then
  echo "1 is smaller than 2";
fi

echo "######################################";
read

# Commands can be connected
# Pipe | redirects output to next command
cat ../templateInstallScript.sh | grep "()";

# && if previous command is successful execute next one
[[ "AB" == "CD" ]] && echo "AB is CD";

## || if previous command fails execute next one
[[ "AB" == "CD" ]] || echo "AB is not CD";

# Next line just checks the condition. The line below checks if it was successful (see $?) and does something
[[ "AB" == "CD" ]];
if [[ "$?" == "0" ]]; then
  echo "AB is CD";
fi


set +vx

echo "######################################";
read

source ../templateInstallScript.sh
echo "######################################";
read

check_if_empty "a";
set +vx
check_if_empty "is";
echo "######################################";
read

touch "testfile";
check_file "testfile";
delete_function "testfile";
echo "######################################";
read

TEST_VARIABLE="testcontent";
check_if_set "TEST_VARIABLE";
echo "######################################";
read

check_if_set "SECOND_TEST_VARIABLE" "defaultcontent";
echo "######################################";
read

check_user "andreas" "527" "/paket2012/home/andreas_house";
echo "######################################";
read

check_diskspace "..." "100000";


exit_script 0;


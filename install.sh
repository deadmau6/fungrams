#!/bin/bash
echo "Checking that python3 and pip are installed."
if ! [ -x "$( command -v python3 )" ]; then
    echo "Error: Python3 not installed."
    exit 1
fi

if ! [ -x "$( command -v pip )" ]; then
    echo "Error: pip not installed."
    exit 1
fi

unset FUNGRAMSPATH 
cd "$(dirname "$0")"
FUNGRAMSPATH="$(pwd)"

res="$(python3 -m pip freeze | grep -oFwf requirements.txt | awk 'BEGIN { ORS="|" } { print $0 }')"
res="(${res::-1})"
missing_installs="$(grep -vE "${res}" requirements.txt | wc -l)"

if [[ $missing_installs != 0 ]]; then
    python3 -m pip install -r "${FUNGRAMSPATH}/requirements.txt"
fi

BASH_ALIASES_PATH="${HOME}/.bash_aliases"
echo "Setting up aliases..."

if ! [ -e $BASH_ALIASES_PATH ]; then
    touch $BASH_ALIASES_PATH
fi

if [[ -z $FGRMS ]] || [[ $FRGMS != $FUNGRAMSPATH ]]; then
    grep -q "${BASH_ALIASES_PATH}" -e "export FGRMS=" && [[ "$?" = 0 ]] && sed -ir 's/^export FGRMS=.*$//' "${BASH_ALIASES_PATH}"
    echo "export FGRMS='${FUNGRAMSPATH}'" >> $BASH_ALIASES_PATH
fi

if [[ -z $FGRMSHELL ]] || [[ $FGRMSHELL != "${FUNGRAMSPATH}/fun_shell.py" ]]; then
    grep -q "${BASH_ALIASES_PATH}" -e "export FGRMSHELL=" && [[ "$?" = 0 ]] && sed -ir 's/^export FGRMSHELL=.*$//' "${BASH_ALIASES_PATH}"
    echo "export FGRMSHELL='${FUNGRAMSPATH}/fun_shell.py'" >> $BASH_ALIASES_PATH
fi

grep -q "${BASH_ALIASES_PATH}" -e "alias fungrams=" && [[ "$?" = 0 ]] && sed -ir 's/^alias fungrams=.*$//' "${BASH_ALIASES_PATH}"
echo 'alias fungrams="python3 $FGRMSHELL"' >> $BASH_ALIASES_PATH

source $BASH_ALIASES_PATH

echo "Done! Restart your shell and then try running:"
echo "fungrams -h"
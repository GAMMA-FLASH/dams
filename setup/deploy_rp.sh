#!/bin/bash

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi

source "$(dirname "$0")/common_utils.sh"

usage() {
    log_message "Usage: $0  [--config <RPG_config_or_directory>] [--version <branch_or_tag_name>] [--attached [RPGNAME]]"
    log_message "Usage: $0 [-c <RPG_config_or_directory>] [-v <branch_or_tag_name>] [-a [RPGNAME]]"
    log_message "RPGNAME one of the ones defined in .cfg"
    exit 1
}

log_setup() {
    echo
    log_message "Deploying gammaflash clients. Selected rpIds: '${ATTACHED_NAMES[*]:-all}'"
    log_message "Branch Name     = ${BRANCH_NAME}"
    echo
}

cli_argparser $@

if [ -z $BRANCH_NAME ]; then
    log_error "branch not definded. "
    usage
fi 

SCRIPT_DIR=$(dirname $0)

UPDATE_SCRIPT="${SCRIPT_DIR}/gfpl/rp/update_rp.sh"
OSC_CONFIG="${OSC_CONFIG:-(dirname $RPG_CONFIG)/CONFIG.xml}"

LOGS="$DAMS/logs/install_dam_rp"

DEF_USER='root'

ssh_update_command() {
    local ip=$1
    command="ssh $DEF_USER@$ip 'bash -s' < $UPDATE_SCRIPT $BRANCH_NAME &> $2"
    echo "starting '$command'"
    eval $command
    command="scp $OSC_CONFIG $DEF_USER@$ip:/root/workspace/dams/dam/CONFIG.xml"
    echo "starting '$command'"
    eval $command
    
    if [[ $? -ne 0 ]]; then
        ((FAILED_COUNT++))
    fi
}

echo "Storing logs in $LOGS"
mkdir -p $LOGS

choose_and_deploy () {
    local HOST=$2
    if [[ " ${ATTACHED_NAMES[*]} " =~ " ${rp_name} " ]] || [ ${#ATTACHED_NAMES[@]} -eq 0  ]; then
            ssh_update_command "$HOST" "$LOGS/update_$HOST.log" &
    fi
}
process_file_with_function choose_and_deploy
wait 

echo "Done"

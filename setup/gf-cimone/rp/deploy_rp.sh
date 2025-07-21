#!/bin/bash

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi

help() {
    echo "deploy_rp [--version <branch_or_tag_name>] [--ip <ip_address>] [--ip <ip_address>] ..."
}

POSITIONAL_ARGS=()
RP_IPS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--ip)
            RP_IPS+=("$2")
            shift # past argument
            shift # past value
            ;;
        -v|--version)
            BRANCH_NAME="$2"
            shift # past argument
            shift # past value
            ;;
        -*|--*)
            echo "Unknown option $1"
            help
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1") # save positional arg
            shift # past argument
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

echo "Branch Name     = ${BRANCH_NAME}"
echo "RP IP Addresses = ${RP_IPS[@]}"


if [[ -n ${POSITIONAL_ARGS[0]} ]]; then
    echo "Last line of file specified as non-opt/last argument:"
    BRANCH_NAME=${POSITIONAL_ARGS[0]}
fi

SCRIPT_DIR=$(dirname $0)

UPDATE_SCRIPT="${SCRIPT_DIR}/update_rp.sh"

LOGS="$DAMS/logs/install_dam_rp"

ssh_update_command() {
    local ip=$1
    command="ssh $ip 'bash -s' < $SCRIPT_DIR/update_rp.sh $BRANCH_NAME &> $2 &"
    echo "starting '$command'"
    eval $command
    
    if [[ $? -ne 0 ]]; then
        ((FAILED_COUNT++))
    fi
}

echo "Storing logs in $LOGS"
mkdir -p $LOGS

if [[ ${#RP_IPS[@]} -eq 1 && ${RP_IPS[0]} == "all" ]]; then
    for i in {101..106}; do
        ssh_update_command "$i" "$LOGS/update_$i.log"
    done
else
    for ip in "${RP_IPS[@]}"; do
        if [[ $ip =~ ^10[1-6]$ ]]; then
		echo $ip
            ssh_update_command "$ip" "$LOGS/update_$ip.log"
        else
            echo "Invalid argument. Please provide a number between 101 and 106."
            exit 1
        fi
    done
fi

wait 

echo "Done"

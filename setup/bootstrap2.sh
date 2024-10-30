# source /opt/gflashenv/bin/activate

BOOTSTRAP_RP="bootstrap2.sh" 
# install bootstrap 2 in all red pitayas
# "scp rp/bootstrap2-rp.sh rp_ip:/root/bootstrap2.sh"

bootstrap() {
    HOST="$1"
    echo -e "\e[32m================ RPG at addr: $HOST ================\e[0m"
    local HOST=$1
    current_time=$(date -u "+%Y-%m-%d %H:%M:%S")  ## take UTC timestamp
    ssh -tt $HOST << EOF
        date -s '$current_time' ;
        bash $BOOTSTRAP_RP ;
        exit
EOF
}

bootstrap "gammasky-rp-dam"
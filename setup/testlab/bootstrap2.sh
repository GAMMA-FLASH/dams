# source /opt/gflashenv/bin/activate

bootstrap() {
    HOST="$1"
    echo -e "\e[32m================ RPG at addr: $HOST ================\e[0m"
    local HOST=$1
    current_time=$(date -u "+%Y-%m-%d %H:%M:%S")  ## take UTC timestamp
    ssh -tt $HOST << EOF
        date -s '$current_time' ;
        bash bootstrap2.sh ;
        exit
EOF
}

bootstrap "gammasky-rp-dam"
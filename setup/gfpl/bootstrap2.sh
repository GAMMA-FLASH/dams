# source /opt/gflashenv/bin/activate

bootstrap() {
    HOST="$1"
    ADDR=$(ssh -G "$HOST" | awk '/^hostname / {print $2}')
    LAST_CHAR=$(echo "$HOST" | rev | cut -c 1)
    echo -e "\e[32m================ RPG$LAST_CHAR at addr: $ADDR ================\e[0m"
    local HOST=$1
    current_time=$(date -u "+%Y-%m-%d %H:%M:%S")  ## take UTC timestamp
    ssh -tt $HOST << EOF
        date -s '$current_time' ;
        bash bootstrap2.sh ;
        exit
EOF
}

bootstrap 101 
bootstrap 102
bootstrap 103
bootstrap 104
bootstrap 105
bootstrap 106


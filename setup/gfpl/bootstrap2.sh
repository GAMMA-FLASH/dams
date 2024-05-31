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

if [ $# -eq 0 ]; then
    for i in {101..106}; do
        bootstrap $i
    done
else
    if [[ $1 =~ ^10[1-6]$ ]]; then
        bootstrap $1
    else
        echo "Invalid argument. Please provide a number between 101 and 106."
        exit 1
    fi
fi

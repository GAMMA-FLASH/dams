source /opt/gflashenv/bin/activate

bootstrap() {
    local target_host=$1
    current_time=$(date "+%Y-%m-%d %H:%M:%S")
    ssh -tt $target_host << EOF
        date -s '$current_time' ;
        bash bootstrap2.sh ;
        exit
EOF
}
echo "RPG1 ================"
bootstrap 101 
echo "RPG2 ================"
bootstrap 102
#ssh -t 102 ". bootstrap.sh"
echo "RPG3 ================"
bootstrap 103
#ssh -t 103 ". bootstrap.sh"
echo "RPG4 ================"
bootstrap 104
#ssh -t 104 ". bootstrap.sh"
echo "RPG5 ================"
bootstrap 105
#ssh -t 105 ". bootstrap.sh"
echo "RPG6 ================"
bootstrap 106
#ssh -t 106 ". bootstrap.sh"

cd workspace/dams/dl0

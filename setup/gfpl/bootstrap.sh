source /opt/gflashenv/bin/activate

echo "RPG1 ================"
current_time=$(date "+%Y-%m-%d %H:%M:%S")
ssh 101 "date -s '$current_time'"
#ssh -t 101 "nohup bash -c './bootstrap.sh' > out 2>&1 &"
echo "RPG2 ================"
current_time=$(date "+%Y-%m-%d %H:%M:%S")
ssh 102 "date -s '$current_time'"
#ssh -t 102 ". bootstrap.sh"
echo "RPG3 ================"
current_time=$(date "+%Y-%m-%d %H:%M:%S")
ssh 103 "date -s '$current_time'"
#ssh -t 103 ". bootstrap.sh"
echo "RPG4 ================"
current_time=$(date "+%Y-%m-%d %H:%M:%S")
ssh 104 "date -s '$current_time'"
#ssh -t 104 ". bootstrap.sh"
echo "RPG5 ================"
current_time=$(date "+%Y-%m-%d %H:%M:%S")
ssh 105 "date -s '$current_time'"
#ssh -t 105 ". bootstrap.sh"
echo "RPG6 ================"
current_time=$(date "+%Y-%m-%d %H:%M:%S")
ssh 106 "date -s '$current_time'"
#ssh -t 106 ". bootstrap.sh"

cd workspace/dams/dl0

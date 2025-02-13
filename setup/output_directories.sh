
INPUT_COMMON=$1

common_path="${INPUT_COMMON:-/home/gamma/workspace/Data/tmpscratch}"
today=$(date +%Y-%m-%d)
DL0DIR_BASE="${common_path}/DL0/${today}"

mkdir -p "${DL0DIR_BASE}"

# Trova l'ultimo numero progressivo
last_num=$(find "${DL0DIR_BASE}" -maxdepth 1 -type d -name "acq_????" \
  | awk -F'_' '{print $NF}' | sort -n | tail -n 1)

next_num=$(printf "%04d" $((10#${last_num:-0} + 1)))


export DL0DIR="${DL0DIR_BASE}/acq_${next_num}"
export DL1DIR="${common_path}/DL1/${today}/acq_${next_num}"
export DL2DIR="${common_path}/DL2/${today}/acq_${next_num}"
echo "=================================================================================="
echo " Common base: '${common_path}' "
echo " Date: '$today'"
echo " Next run: '$next_num'"
echo "    > DL0DIR: '$DL0DIR'"
echo "    > DL1DIR: '$DL1DIR'"
echo "    > DL2DIR: '$DL2DIR'"
echo "=================================================================================="
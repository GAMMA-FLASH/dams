#!/bin/bash

# Cartelle di input
DL0="/home/worker/workspace/testgammaflash/dams/pipe/test/Data/DL0/acquisizione_2022_07_01_rpg0"
DL1="/home/worker/workspace/testgammaflash/dams/pipe/test/Data/DL1/acquisizione_2022_07_01_rpg0"

# Trova i nomi dei file in DL0
files_DL0=$(find "$DL0" -type f -name "*.h5" -exec basename {} \; | sed 's/\.h5$//')

# Trova i nomi dei file in DL1
files_DL1=$(find "$DL1" -type f -name "*.dl1.h5" -exec basename {} \; | sed 's/\.dl1.h5$//')

# Trova i nomi dei file unici
all_files=$(echo -e "$files_DL0\n$files_DL1" | sort | uniq)

# Trova i nomi dei file che non hanno corrispondenza in entrambe le cartelle
for file in $all_files; do
    if [[ ! "$files_DL0" =~ "$file" && ! "$files_DL1" =~ "$file" ]]; then
        echo "$file"
    fi
done

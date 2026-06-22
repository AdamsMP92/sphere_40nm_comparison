#!/bin/bash

start_ns=$(date +%s%N)

mkdir ./MagData
mkdir ./HystData
mkdir ./MagData/Orientation_1

# run mumax3 simulation
./mumax3 IronSphere_UniaxialAni.mx3

end_ns=$(date +%s%N)
elapsed_ns=$((end_ns - start_ns))
elapsed_s=$(awk "BEGIN {printf \"%.3f\", $elapsed_ns/1000000000}")
echo "Elapsed wall-clock time: ${elapsed_s} s"

# number of ovf files
N_Fields=$(find ./IronSphere_UniaxialAni.out -name *.ovf | wc -l)

Field_Counter=0
Field_File_Counter=1

while (( Field_Counter < N_Fields ))
do
    filename="$(printf "./IronSphere_UniaxialAni.out/m%06d.ovf" "$Field_Counter")"
    ./mumax3-convert -gplot "$filename"

    filename2="$(printf "./IronSphere_UniaxialAni.out/m%06d.gplot" "$Field_Counter")"
    filename3="./IronSphere_UniaxialAni.out/m_$Field_File_Counter.gplot"

    mv -- $filename2 $filename3
    cp $filename3 ./MagData/Orientation_1/

    ((Field_Counter++))
    ((Field_File_Counter++))
done

# hysteresis data
filename2="./IronSphere_UniaxialAni.out/table.txt"
filename3="./IronSphere_UniaxialAni.out/Hysteresis_1.txt"

mv -- $filename2 $filename3
cp $filename3 ./HystData/

# clean up
rm -rf "./IronSphere_UniaxialAni.out/"

end_ns=$(date +%s%N)
elapsed_ns=$((end_ns - start_ns))
elapsed_s=$(awk "BEGIN {printf \"%.3f\", $elapsed_ns/1000000000}")
echo "Elapsed wall-clock time: ${elapsed_s} s"

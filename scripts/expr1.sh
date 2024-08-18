#!/bin/bash
# Experiment 1: Conflicts vs. detection time
# Run experiment 1. First section generates log files, second section generates
# action constraints and measures detection time

# for (( i = 0 ; i < 4; i++)); do
#     python3 scripts/expr1_log_generation.py
# done

outfile="${1}"

printf "logfile,conflicts,time0,time1,time2\n" >> $outfile

for log in results/expr_1/logs/*
do
	for (( i = 0; i < 25; i += 2 ))
	do
		time0=$(python3 scripts/expr1_detection.py $i $log)
		time1=$(python3 scripts/expr1_detection.py $i $log)
		time2=$(python3 scripts/expr1_detection.py $i $log)
		printf "%s,%s,%s,%s,%s\n" $log $i $time0 $time1 $time2 >> $outfile
	done
done


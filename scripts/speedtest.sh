#!/bin/sh -ex

mkdir -p speedtest
cat /proc/cpuinfo > speedtest/cpuinfo.txt
lshw > speedtest/lshw.txt

(Stockfish/src/stockfish-x86-64-avx2 speedtest 2>&1 | tee speedtest/speedtest-x86-64-avx2.txt)
(Stockfish/src/stockfish-x86-64-bmi2 speedtest 2>&1 | tee speedtest/speedtest-x86-64-bmi2.txt) || echo "ERROR: no bmi2"
(Stockfish/src/stockfish-x86-64-avxvnni speedtest 2>&1 | tee speedtest/speedtest-x86-64-avxvnni.txt) || echo "ERROR: no avxvnni"
(Stockfish/src/stockfish-x86-64-avx512 speedtest 2>&1 | tee speedtest/speedtest-x86-64-avx512.txt) || echo "ERROR: no avx512"
(Stockfish/src/stockfish-x86-64-vnni512 speedtest 2>&1 | tee speedtest/speedtest-x86-64-vnni512.txt) || echo "ERROR: no vnni512"
(Stockfish/src/stockfish-x86-64-avx512icl speedtest 2>&1 | tee speedtest/speedtest-x86-64-avx512icl.txt) || echo "ERROR: no avx512icl"

threads=$(nproc --ignore 1)
(Stockfish/src/stockfish-x86-64-avx2 speedtest $threads 2>&1 | tee speedtest/speedtest-x86-64-avx2-$threads.txt)
(Stockfish/src/stockfish-x86-64-bmi2 speedtest $threads 2>&1 | tee speedtest/speedtest-x86-64-bmi2-$threads.txt) || echo "ERROR: no bmi2"
(Stockfish/src/stockfish-x86-64-avxvnni speedtest $threads 2>&1 | tee speedtest/speedtest-x86-64-avxvnni-$threads.txt) || echo "ERROR: no avxvnni"
(Stockfish/src/stockfish-x86-64-avx512 speedtest $threads 2>&1 | tee speedtest/speedtest-x86-64-avx512-$threads.txt) || echo "ERROR: no avx512"
(Stockfish/src/stockfish-x86-64-vnni512 speedtest $threads 2>&1 | tee speedtest/speedtest-x86-64-vnni512-$threads.txt) || echo "ERROR: no vnni512"
(Stockfish/src/stockfish-x86-64-avx512icl speedtest $threads 2>&1 | tee speedtest/speedtest-x86-64-avx512icl-$threads.txt) || echo "ERROR: no avx512icl"

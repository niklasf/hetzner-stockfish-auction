#!/bin/sh -ex

apt update && apt install -y ca-certificates curl

curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" \
  > /etc/apt/sources.list.d/docker.list

apt update
apt dist-upgrade -y
apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-compose-plugin \
  build-essential \
  git \
  tmux \
  btop \
  lshw \
  mosh

git clone https://github.com/official-stockfish/Stockfish.git
git clone https://github.com/official-stockfish/docker-fishtest.git

(cd Stockfish/src && make clean && make -j profile-build ARCH=x86-64-avx2 EXE=stockfish-x86-64-avx2)
(cd Stockfish/src && make clean && make -j profile-build ARCH=x86-64-bmi2 EXE=stockfish-x86-64-bmi2 || echo "ERROR: no bmi2")
(cd Stockfish/src && make clean && make -j profile-build ARCH=x86-64-avxvnni EXE=stockfish-x86-64-avxvnni || echo "ERROR: no avxvnni")
(cd Stockfish/src && make clean && make -j profile-build ARCH=x86-64-avx512 EXE=stockfish-x86-64-avx512 || echo "ERROR: no avx512")
(cd Stockfish/src && make clean && make -j profile-build ARCH=x86-64-vnni512 EXE=stockfish-x86-64-vnni512 || echo "ERROR: no vnni512")
(cd Stockfish/src && make clean && make -j profile-build ARCH=x86-64-avx512icl EXE=stockfish-x86-64-avx512icl || echo "ERROR: no avx512icl")

read -p "consider rebooting"

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

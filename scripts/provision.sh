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

echo "done. consider rebooting"

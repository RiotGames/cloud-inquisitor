#!/bin/bash

wait_apt_lock() {
    while pgrep apt >/dev/null 2>&1 ; do
        sleep 0.5
    done
}

wait_apt_lock
apt-get update
wait_apt_lock
apt-get -qq install git make

git clone --single-branch -b $1 https://github.com/RiotGames/cloud-inquisitor.git
cd cloud-inquisitor
wait_apt_lock
make $2
make enable_supervisor

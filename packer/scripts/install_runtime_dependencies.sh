#!/bin/bash -e

install_requirements() {
    echo "Installing requirements"

    # Ubuntu's cloud images has cloud-init doing an apt-get update / upgrade on first boot
    echo "Waiting for apt-get update, this may take a few minutes"
    while pgrep apt >/dev/null 2>&1 ; do
        sleep 0.5
    done
    sudo apt-get update

    if [ "${APP_APT_UPGRADE}" != "False" ]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
    fi

    # Ensure curl is installed for the next step
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y curl

    # Not using Ubuntu distro node 4.x package due to intermittent bug cases
    curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -

    # We're mixing build with with runtime a bit here (git, npm). Consider separating build-deps (git npm)
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip nginx libxml2-dev libxmlsec1-dev \
        python3-dev mysql-client libmysqlclient-dev libncurses5-dev swig \
        supervisor libffi-dev libsasl2-dev libldap2-dev git nodejs 

    # Update pip to fix bug in 8.1.1
    sudo -H pip3 install --upgrade pip virtualenv
}

install_requirements

.PHONY: install_libs install_services install_files init_services init_cinq enable_test do_test setup_localdev setup_tarvisci

PATH_CINQ ?= /opt/cinq
PATH_FRONTEND = ${PATH_CINQ}/cinq-frontend
PATH_BACKEND ?= ${PATH_CINQ}/cinq-backend
PATH_VENV = ${PATH_CINQ}/cinq-venv
PATH_PYTHON ?= /usr/bin/python3
SECRET_KEY ?= $(shell openssl rand -hex 32)
APP_DB_URI ?= "mysql://cinq:secretpass@127.0.0.1:3306/cinq_dev"
INS_DIR = ${CURDIR}

install_libs_tarvisci:
	curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
	apt-get install -qq build-essential apt-transport-https ca-certificates libffi-dev libldap2-dev libmysqlclient-dev libncurses5-dev libsasl2-dev libxml2-dev libxmlsec1-dev python3-dev software-properties-common swig nodejs

install_libs:
	apt-get update
	apt-get install -qq curl build-essential apt-transport-https ca-certificates git libffi-dev libldap2-dev libmysqlclient-dev libncurses5-dev libsasl2-dev libxml2-dev libxmlsec1-dev mysql-client python3-dev software-properties-common swig
	curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
	apt-get update
	apt-get install -qq nodejs
	curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
	python3 /tmp/get-pip.py
	pip3 install -U virtualenv

install_services:
	apt-get update
	apt-get -qq install mysql-server nginx

install_files:
	# Prepare directories
	mkdir -p /var/log/cloud-inquisitor/
	chown -R ${SUDO_USER}:${SUDO_USER} /var/log/cloud-inquisitor/
	mkdir -p ${PATH_CINQ}

	# Checkout frontend code
	sudo git clone https://github.com/RiotGames/cinq-frontend.git ${PATH_FRONTEND}

	# Target is not backend means this is a build job for plugins, therefore we need to checkout backend code as well
	if [ "${PATH_BACKEND}" != "." ]; then \
		sudo git clone https://github.com/RiotGames/cloud-inquisitor.git ${PATH_BACKEND}; \
	fi

	chown -R ${SUDO_USER}:${SUDO_USER} ${PATH_CINQ}

	# Setup frontend and virtual env
	cd ${PATH_FRONTEND}; sudo -u ${SUDO_USER} -H npm i; sudo -u ${SUDO_USER} -H node_modules/.bin/gulp build.dev
	sudo -u ${SUDO_USER} -H virtualenv --python=${PATH_PYTHON} ${PATH_VENV}

	# Setup Keys
	sudo -u ${SUDO_USER} -H sh -c 'mkdir -p ~/.cinq/ssl'
	openssl genrsa -out private.key 2048
	sudo -H mv private.key ~/.cinq/ssl

	# Prepare Cinq config file
	sudo -H cp -f ${INS_DIR}/packer/files/logging.json ~/.cinq
	sed -e "s|APP_DB_URI|${APP_DB_URI}|" -e "s|APP_SECRET_KEY|${SECRET_KEY}|" -e "s|APP_USE_USER_DATA|false|" ${INS_DIR}/packer/files/backend-config.json > ${INS_DIR}/packer/files/config.json
	sudo -H cp -f ${INS_DIR}/packer/files/config.json ~/.cinq
	sudo -H chown -R ${SUDO_USER}:${SUDO_USER} ~/.cinq

init_services:
	# Create Cinq MySQL account
	sudo mysql -u root -e "create database cinq_dev; grant all privileges on *.* to 'cinq'@'localhost' identified by 'secretpass';" || true

	# NGINX configuration
	sed -e "s|APP_FRONTEND_BASE_PATH|${PATH_FRONTEND}/dist|g" ${INS_DIR}/packer/files/nginx-nossl.conf > /etc/nginx/sites-available/cinq.conf
	rm -f /etc/nginx/sites-enabled/default
	ln -sf /etc/nginx/sites-available/cinq.conf /etc/nginx/sites-enabled/cinq.conf
	service nginx restart

init_cinq:

	# Target is not backend means this is a build job for plugins, therefore we need to pip install plugin as well
	if [ "${PATH_BACKEND}" != "." ]; then \
		sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pip3 install -e .; \
	fi

	# Install backend
	cd ${PATH_BACKEND}/backend; sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pip3 install -e .

	# Initialize Cinq backend
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/cloud-inquisitor db upgrade
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/cloud-inquisitor setup

enable_test:
	echo "WARNING: Running Cinq test will DESTROY your data in your database. Please make sure you run it on a dedicated test environment"
	sed -i -E "s/\"test_mode\": ([a-z]+)/\"test_mode\": true/g" ~/.cinq/config.json

do_test:
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pip3 install -U pytest moto[server]==1.3.4
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pytest ${PATH_BACKEND}/backend

setup_localdev: install_libs install_services install_files init_services init_cinq

setup_tarvisci: install_libs_tarvisci install_files init_services init_cinq enable_test

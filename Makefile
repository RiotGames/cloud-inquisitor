.PHONY: install_libs install_services install_files init_services init_cinq enable_test do_test setup_localdev setup_tarvisci

PATH_CINQ ?= /opt/cinq
PATH_BACKEND ?= ${PATH_CINQ}/backend
PATH_FRONTEND ?= ${PATH_CINQ}/frontend
PATH_PYTHON ?= /usr/bin/python3
PATH_VENV ?= ${PATH_CINQ}/cinq-venv
APP_WORKER_PROCS ?= 12
APP_CONFIG_BASE_PATH ?= /usr/local/etc/cloud-inquisitor
APP_DB_URI ?= "mysql://cinq:secretpass@127.0.0.1:3306/cinq_dev"
APP_KMS_ACCOUNT_NAME ?= account
APP_KMS_REGION ?= us-west-2
APP_USER_DATA_URL ?= "http://169.254.169.254/latest/user-data"
APP_AWS_API_ACCESS_KEY ?= ""
APP_AWS_API_SECRET_KEY ?= ""
INS_DIR = ${CURDIR}
SECRET_KEY ?= $(shell openssl rand -hex 32)
USE_HTTPS ?= false
USE_USER_DATA ?= false

install_libs_tarvisci:
	curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
	apt-get install -qq build-essential apt-transport-https ca-certificates libffi-dev libldap2-dev libmysqlclient-dev libncurses5-dev libsasl2-dev libxml2-dev libxmlsec1-dev mysql-client nodejs nginx python3-dev software-properties-common swig

install_libs:
	apt-get update
	apt-get install -qq curl build-essential apt-transport-https ca-certificates git libffi-dev libldap2-dev libmysqlclient-dev libncurses5-dev libsasl2-dev libxml2-dev libxmlsec1-dev mysql-client python3-dev software-properties-common supervisor swig
	curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
	apt-get update
	apt-get install -qq nodejs
	curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
	python3 /tmp/get-pip.py
	pip3 install -U virtualenv

install_service_mysql:
	apt-get -qq install mysql-server

install_service_nginx:
	apt-get -qq install nginx

install_files:
	# Prepare directories
	mkdir -p /var/log/cloud-inquisitor/
	chmod -R 777 /var/log/cloud-inquisitor/
	mkdir -p ${PATH_CINQ}

	# Copy project files
	cp -R ${INS_DIR}/backend ${PATH_BACKEND}
	cp -R ${INS_DIR}/frontend ${PATH_FRONTEND}
	cp -R ${INS_DIR}/plugins ${PATH_CINQ}/plugins
	cp -R ${INS_DIR}/docs ${PATH_CINQ}/docs
	chown -R ${SUDO_USER}:${SUDO_USER} ${PATH_CINQ}

	# Setup frontend and virtual env
	cd ${PATH_FRONTEND}; sudo -u ${SUDO_USER} -H npm i; sudo -u ${SUDO_USER} -H node_modules/.bin/gulp build.dev
	sudo -u ${SUDO_USER} -H virtualenv --python=${PATH_PYTHON} ${PATH_VENV}

	# Setup Keys
	sudo -H sh -c 'mkdir -p ${APP_CONFIG_BASE_PATH}/ssl'
	openssl genrsa -out private.key 2048
	sudo -H mv private.key ${APP_CONFIG_BASE_PATH}/ssl

	# Prepare Cinq config file
	sudo -H cp -f ${INS_DIR}/resources/config_files/logging.json ${APP_CONFIG_BASE_PATH}
	sed -e "s|APP_DB_URI|${APP_DB_URI}|g" -e "s|APP_SECRET_KEY|${SECRET_KEY}|g" -e "s|APP_USE_USER_DATA|${USE_USER_DATA}|g" -e "s|APP_KMS_ACCOUNT_NAME|${APP_KMS_ACCOUNT_NAME}|g" -e "s|APP_KMS_REGION|${APP_KMS_REGION}|g" -e "s|APP_USER_DATA_URL|${APP_USER_DATA_URL}|g" -e "s|APP_AWS_API_ACCESS_KEY|${APP_AWS_API_ACCESS_KEY}|g" -e "s|APP_AWS_API_SECRET_KEY|${APP_AWS_API_SECRET_KEY}|g" ${INS_DIR}/resources/config_files/backend-config.json > ${APP_CONFIG_BASE_PATH}/config.json
	sudo -H chown -R ${SUDO_USER}:${SUDO_USER} ${APP_CONFIG_BASE_PATH}

init_service_mysql:
	# Create Cinq MySQL account
	sudo mysql -u root -e "create database cinq_dev; grant all privileges on *.* to 'cinq'@'localhost' identified by 'secretpass';" || true

init_service_nginx:
	# NGINX configuration
	if [ "${USE_HTTPS}" != "false" ]; then \
		sed -e "s|APP_FRONTEND_BASE_PATH|${PATH_FRONTEND}/dist|g" -e "s|APP_CONFIG_BASE_PATH|${APP_CONFIG_BASE_PATH}|g" ${INS_DIR}/resources/config_files/nginx-ssl.conf > /etc/nginx/sites-available/cinq.conf; \
		mkdir -p ${PATH_CINQ}/ssl; \
		openssl req -x509 -subj "/C=US/ST=CA/O=Your Company/localityName=Your City/commonName=localhost/organizationalUnitName=Operations/emailAddress=someone@example.com" -days 3650 -newkey rsa:2048 -nodes -keyout ${APP_CONFIG_BASE_PATH}/ssl/cinq-frontend.key -out ${APP_CONFIG_BASE_PATH}/ssl/cinq-frontend.crt; \
	else \
		sed -e "s|APP_FRONTEND_BASE_PATH|${PATH_FRONTEND}/dist|g" ${INS_DIR}/resources/config_files/nginx-nossl.conf > /etc/nginx/sites-available/cinq.conf; \
	fi

	rm -f /etc/nginx/sites-enabled/default
	ln -sf /etc/nginx/sites-available/cinq.conf /etc/nginx/sites-enabled/cinq.conf
	service nginx restart

init_cinq:
	# Install backend
	cd ${PATH_BACKEND}; sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pip3 install -e .

	# Install plugins
	cd ${PATH_CINQ}; sudo -u ${SUDO_USER} -H find plugins -mindepth 2 -maxdepth 2 -type d -name "cinq-*" -exec ${PATH_VENV}/bin/pip3 install -e {} \;

init_cinq_db:
	# Initialize Cinq DB
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/cloud-inquisitor db upgrade

enable_supervisor:
	sed -e "s|APP_CONFIG_BASE_PATH|${APP_CONFIG_BASE_PATH}|g" -e "s|APP_PYENV_PATH|${PATH_VENV}|g" -e "s|APP_WORKER_PROCS|${APP_WORKER_PROCS}|g" ${INS_DIR}/resources/config_files/supervisor.conf > /etc/supervisor/conf.d/cinq.conf

enable_test:
	echo "WARNING: Running Cinq test will DESTROY your data in your database. Please make sure you run it on a dedicated test environment"
	sed -i -E "s/\"test_mode\": ([a-z]+)/\"test_mode\": true/g" ${APP_CONFIG_BASE_PATH}/config.json

do_test:
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pip3 install -U pytest moto[server]==1.3.7
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/cloud-inquisitor setup
	sudo -u ${SUDO_USER} -H ${PATH_VENV}/bin/pytest ${PATH_BACKEND}

clean:
	sudo rm -rf ${PATH_CINQ} ${PATH_BACKEND} ${PATH_FRONTEND} ${PATH_VENV} ${APP_CONFIG_BASE_PATH}

setup_localdev: install_libs install_service_mysql install_service_nginx install_files init_service_mysql init_service_nginx init_cinq init_cinq_db

setup_tarvisci: install_libs_tarvisci install_files init_service_mysql init_service_nginx init_cinq init_cinq_db enable_test

setup_server_install: install_libs install_service_nginx install_files init_service_nginx init_cinq

reinstall_localdev: clean install_files init_cinq
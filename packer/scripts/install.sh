#!/bin/bash -e

validate_environment() {
    echo "Validating environment"
    if [ -z "${APP_TEMP_BASE}" ]; then echo "Missing APP_TEMP_BASE environment variable" && exit -1; fi
    if [ -z "${APP_DEBUG}" ]; then echo "Missing APP_DEBUG environment variable" && exit -1; fi
    if [ -z "${APP_PYENV_PATH}" ]; then echo "Missing APP_PYENV_PATH environment variable" && exit -1; fi
    if [ -z "${APP_FRONTEND_BASE_PATH}" ]; then echo "Missing APP_FRONTEND_BASE_PATH environment variable" && exit -1; fi
    if [ -z "${APP_BACKEND_BASE_PATH}" ]; then echo "Missing APP_BACKEND_BASE_PATH environment variable" && exit -1; fi
    if [ -z "${APP_DB_URI}" ]; then echo "Missing APP_DB_URI environment variable" && exit -1; fi
    if [ -z "${APP_SSL_ENABLED}" ]; then echo "Missing APP_SSL_ENABLED environment variable" && exit -1; fi
    if [ -z "${APP_USE_USER_DATA}" ]; then echo "Missing APP_USE_USER_DATA environment variable" && exit -1; fi
    if [ -z "${APP_KMS_ACCOUNT_NAME}" ]; then echo "Missing APP_KMS_ACCOUNT_NAME environment variable" && exit -1; fi
    if [ -z "${APP_USER_DATA_URL}" ]; then echo "Missing APP_USER_DATA_URL environment variable" && exit -1; fi
}

create_virtualenv() {
    echo "Setting up python virtualenv"

    if [ -d "${APP_PYENV_PATH}" ]; then
        echo "VirtualEnv folder already exists, skipping"
    else
        virtualenv -p python3 "${APP_PYENV_PATH}"
    fi
}

install_backend() {
    python=${APP_PYENV_PATH}/bin/python3
    pip=${APP_PYENV_PATH}/bin/pip3

    echo "Installing backend"
    mkdir -p ${APP_BACKEND_BASE_PATH}
    cp -a ${APP_TEMP_BASE}/cinq-backend/* ${APP_BACKEND_BASE_PATH}

    # setup.py to prepare for dynamic module reloading.
    # TODO: Remove PBR_VERSION once we are building CInq as a package
    (
        cd ${APP_BACKEND_BASE_PATH}
        PBR_VERSION=1.7.0 $python setup.py install

        $pip install -r riot-plugins.txt
        $pip install --upgrade -r ${APP_BACKEND_BASE_PATH}/requirements.txt

        # Create log folders for the application and allow the backend user to write to them
        mkdir -p logs
        chown -R www-data:www-data logs
    )
}

install_frontend() {
    FRONTEND_TEMP_BASE=${APP_TEMP_BASE}/cinq-frontend
    pushd ${FRONTEND_TEMP_BASE}
        # Delete node_modules and dist if they exist to prevent
        # bad versions being used
        if [ -d node_modules ]; then rm -rf node_modules; fi
        if [ -d dist ]; then rm -rf dist; fi

        echo "Installing NPM modules"
        npm i --quiet

        echo "Building frontend application"
        ./node_modules/.bin/gulp build.prod
    popd

    mkdir -p ${APP_FRONTEND_BASE_PATH}
    cp -a ${FRONTEND_TEMP_BASE}/dist/* ${APP_FRONTEND_BASE_PATH}
}

configure_application() {
    echo "Configuring backend"
    SECRET_KEY=$(openssl rand -hex 32)
    sed -e "s|APP_DEBUG|${APP_DEBUG}|" \
        -e "s|APP_DB_URI|${APP_DB_URI}|" \
        -e "s|APP_SECRET_KEY|${SECRET_KEY}|" \
        -e "s|APP_USE_USER_DATA|${APP_USE_USER_DATA}|" \
        -e "s|APP_USER_DATA_URL|${APP_USER_DATA_URL}|" \
        -e "s|APP_KMS_ACCOUNT_NAME|${APP_KMS_ACCOUNT_NAME}|" \
        -e "s|APP_INSTANCE_ROLE_ARN|${APP_INSTANCE_ROLE_ARN}|" \
        -e "s|APP_AWS_API_ACCESS_KEY|${APP_AWS_API_ACCESS_KEY}|" \
        -e "s|APP_AWS_API_SECRET_KEY|${APP_AWS_API_SECRET_KEY}|" \
        files/backend-settings.py > ${APP_BACKEND_BASE_PATH}/settings/production.py
}

install_certs() {
    if [ -z "$APP_SSL_CERT_DATA" -o -z "$APP_SSL_KEY_DATA" ]; then
        echo "Certificate or key data missing, installing self-signed cert"
        generate_self_signed_certs
    else
        echo "Installing certificates"
        CERTDATA=$(echo "$APP_SSL_CERT_DATA" | base64 -d)
        KEYDATA=$(echo "$APP_SSL_KEY_DATA" | base64 -d)

        echo "$CERTDATA" > $APP_BACKEND_BASE_PATH/settings/ssl/cinq-frontend.crt
        echo "$KEYDATA" > $APP_BACKEND_BASE_PATH/settings/ssl/cinq-frontend.key
    fi
}

function generate_jwt_key() {
    echo "Generating JWT private key"
    openssl genrsa -out ${APP_BACKEND_BASE_PATH}/settings/ssl/private.key 2048
}

generate_self_signed_certs() {
    CERTINFO="/C=US/ST=CA/O=Your Company/localityName=Your City/commonName=localhost/organizationalUnitName=Operations/emailAddress=someone@example.com"
    openssl req -x509 -subj "$CERTINFO" -days 3650 -newkey rsa:2048 -nodes \
        -keyout ${APP_BACKEND_BASE_PATH}/settings/ssl/cinq-frontend.key \
        -out ${APP_BACKEND_BASE_PATH}/settings/ssl/cinq-frontend.crt
}

configure_nginx() {
    if [ "${APP_SSL_ENABLED}" = "True" ]; then
        echo "Configuring nginx with ssl"
        NGINX_CFG="nginx-ssl.conf"
    else
        echo "Configuring nginx without ssl"
        NGINX_CFG="nginx-nossl.conf"
    fi

    sed -e "s|APP_FRONTEND_BASE_PATH|${APP_FRONTEND_BASE_PATH}|g" \
        -e "s|APP_BACKEND_BASE_PATH|${APP_BACKEND_BASE_PATH}|g" \
        files/${NGINX_CFG} > /etc/nginx/sites-available/cinq.conf

    rm -f /etc/nginx/sites-enabled/default;
    ln -sf /etc/nginx/sites-available/cinq.conf /etc/nginx/sites-enabled/cinq.conf
    # redirect output to assign in-function stdout/err to global
    service nginx restart 1>&1 2>&2
}

configure_supervisor() {
    echo "Configuring supervisor"
    sed -e "s|APP_BACKEND_BASE_PATH|${APP_BACKEND_BASE_PATH}|g" \
        -e "s|APP_PYENV_PATH|${APP_PYENV_PATH}|g" \
        files/supervisor.conf > /etc/supervisor/conf.d/cinq.conf

    # If running on a systemd enabled system, ensure the service is enabled and running
    if [ ! -z "$(which systemctl)" ]; then
        systemctl enable supervisor.service
    else
        update-rc.d supervisor enable
    fi
}

cd ${APP_TEMP_BASE}

validate_environment
create_virtualenv
install_frontend
install_backend
install_certs
generate_jwt_key
configure_application
configure_supervisor
configure_nginx

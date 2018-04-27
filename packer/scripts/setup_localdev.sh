#!/bin/bash

echo "----- START | Initialization phase 1 -----"
apt-get update
apt-get upgrade -y
apt-get install -y curl build-essential apt-transport-https ca-certificates git libffi-dev libldap2-dev libmysqlclient-dev libncurses5-dev libsasl2-dev libxml2-dev libxmlsec1-dev mysql-client nginx python3-dev software-properties-common swig

curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

apt-get update
apt-get install -y docker-ce nodejs

curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py
pip3 install -U virtualenv

curl -L https://github.com/docker/compose/releases/download/1.19.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

sudo -u `logname` -H sh -c 'mkdir -p ~/.cinq/ssl'
mkdir -p /proj/docker
mkdir -p /proj/tmp
echo "----- END | Initialization phase 1 -----"

echo "----- START | Docker configurations -----"
cat >/proj/docker/docker-compose.yml <<EOL
version: '3'

services:

  cinq-dev-db:
    image: mysql:5.7
    container_name: cinq_db
    restart: always
    ports:
      - "127.0.0.1:3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=mypassword
      - MYSQL_DATABASE=cinq_dev
      - MYSQL_USER=${DB_USER:-cinq}
      - MYSQL_PASSWORD=${DB_PASS:-changeme}
    volumes:
      - "../volumes/cinq-dev-db:/var/lib/mysql"
EOL
usermod -aG docker `logname`
pushd /proj/docker
docker-compose up 1>/dev/null 2>/dev/null &
popd
echo "----- END | Docker configurations -----"

echo "----- START | Initialization phase 2 -----"
chown -R `logname`:`logname` /proj
pushd /proj
echo "----- END | Initialization phase 2 -----"

echo "----- START | Frontend setup -----"
sudo -u `logname` -H git clone https://github.com/RiotGames/cinq-frontend.git
pushd cinq-frontend
sudo -u `logname` -H npm i
sudo -u `logname` -H node_modules/.bin/gulp build.dev
popd
echo "----- END | Frontend setup -----"

echo "----- START | NGINX setup -----"
mkdir -p /etc/nginx/ssl
CERTINFO="/C=US/ST=CA/O=Your Company/localityName=Your City/commonName=localhost/organizationalUnitName=Operations/emailAddress=someone@example.com"
openssl req -x509 -subj "$CERTINFO" -days 3650 -newkey rsa:4096 -nodes -keyout /etc/nginx/ssl/cinq-frontend.key -out /etc/nginx/ssl/cinq-frontend.crt

mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.old
cat >/etc/nginx/nginx.conf <<EOL
worker_processes  1;

events {
    worker_connections  1024;
}


http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;

    keepalive_timeout  65;

    include sites-enabled/*;
}
EOL

rm /etc/nginx/sites-enabled/default
cat >/etc/nginx/sites-enabled/default <<EOL
server {
    listen 80 default_server;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl default_server;

    # SSL Certificates
    ssl_certificate /etc/nginx/ssl/cinq-frontend.crt;
    ssl_certificate_key /etc/nginx/ssl/cinq-frontend.key;

    root /proj/cinq-frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~ ^/(api|saml|auth)/ {
        proxy_pass http://localhost:5000;
        proxy_redirect off;
        proxy_buffering off;
        proxy_read_timeout 30s;
        proxy_cache off;
        expires off;

        proxy_set_header    Host            \$host;
        proxy_set_header    X-Real-IP       \$remote_addr;
        proxy_set_header    X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOL
service nginx restart
echo "----- END | NGINX setup -----"

echo "----- START | Backend setup -----"
mkdir -p /var/log/cloud-inquisitor/
chown -R `logname`:`logname` /var/log/cloud-inquisitor/

sudo -u `logname` -H virtualenv cinq-dev
sudo -u `logname` -H git clone https://github.com/RiotGames/cloud-inquisitor.git

cat >/proj/tmp/config.json <<EOL
{
    "log_level": "DEBUG",
    "test_mode": false,
    "use_user_data": false,
    "kms_account_name": "YOUR_AWS_ACCOUNT_NAME_HERE",
    "kms_region": "AWS_REGION_HERE",

    "aws_api": {
        "instance_role_arn": "arn:aws:iam::YOUR_AWS_ACCOUNT_NUMBER_HERE:role/CloudInquisitorInstanceProfile",
        "access_key": "YOUR_AWS_ACCESS_KEY_HERE",
        "secret_key": "YOUR_AWS_SECRET_KEY_HERE"
    },

    "database_uri": "mysql://cinq:changeme@127.0.0.1:3306/cinq_dev",

    "flask": {
        "secret_key": "random_generated_string",
        "json_sort_keys": false
    }
}
EOL

cat >/proj/tmp/logging.json <<EOL
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "rainbow": {
            "datefmt": "[%H:%M:%S]",
            "format": "%(asctime)s %(name)s %(message)s"
        },
        "standard": {
            "datefmt": "[%H:%M:%S]",
            "format": "%(asctime)s %(name)s [%(levelname)s] %(message)s"
        }
    },
    "filters": {
        "standard": {
            "()": "cloud_inquisitor.log.LogLevelFilter"
        }
    },
    "handlers": {
        "console": {
            "formatter": "rainbow",
            "datefmt": "[%H:%M:%S]",
            "stream": "ext://sys.stdout",
            "color_asctime": [ null, null, null ],
            "color_message_warning": [ "yellow", null, true ],
            "color_name": [ "green", null, false ],
            "class": "rainbow_logging_handler.RainbowLoggingHandler",
            "filters": ["standard"]
        },
        "file": {
            "filename": "/var/log/cloud-inquisitor/default.log",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": 7,
            "formatter": "standard",
            "filters": ["standard"]
        },
        "file.http": {
            "filename": "/var/log/cloud-inquisitor/apiserver.log",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": 7,
            "formatter": "standard",
            "filters": ["standard"]
        },
        "file.scheduler": {
            "filename": "/var/log/cloud-inquisitor/scheduler.log",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": 7,
            "formatter": "standard",
            "filters": ["standard"]
        },
        "database": {
            "class": "cloud_inquisitor.log.DBLogger",
            "min_level": "WARNING"
        }
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": [
                "file",
                "console",
                "database"
            ]
        },
        "cloud_inquisitor": {
            "level": "DEBUG",
            "propagate": false,
            "handlers": [
                "console",
                "database"
            ]
        },
        "apscheduler": {
            "level": "WARNING",
            "propagate": false,
            "handlers": [
                "file",
                "console",
                "database"
            ]
        },
        "boto3": {
            "level": "WARNING",
            "propagate": false,
            "handlers": [
                "console",
                "file",
                "database"
            ]
        },
        "botocore": {
            "level": "WARNING",
            "propagate": false,
            "handlers": [
                "console",
                "file",
                "database"
            ]
        },
        "parso": {
            "level": "WARNING",
            "propagate": "false"
        },
        "git": {
            "level": 100,
            "propagate": "false"
        },
        "requests": {
            "level": "WARNING",
            "propagate": false,
            "handlers": [
                "console",
                "file"
            ]
        },
        "pyexcel": {
            "level": 100,
            "propagate": "false"
        },
        "pyexcel_io": {
            "level": 100,
            "propagate": "false"
        },
        "urllib3": {
            "level": 100,
            "propagate": "false"
        },
        "werkzeug": {
            "level": "INFO",
            "propagate": false,
            "handlers": [
                "console",
                "file.http"
            ]
        }
    }
}
EOL

pushd /proj/tmp
openssl genrsa -out private.key 2048
sudo -H mv private.key ~/.cinq/ssl
popd

sudo -H cp /proj/tmp/logging.json ~/.cinq
sudo -H cp /proj/tmp/config.json ~/.cinq
sudo -H chown -R `logname`:`logname` ~/.cinq

pushd /proj/cloud-inquisitor/backend
sudo -u `logname` -H /proj/cinq-dev/bin/pip3 install -e .
sudo -u `logname` -H /proj/cinq-dev/bin/cloud-inquisitor db upgrade
popd

echo "----- END | Backend setup -----"

echo "----- START | Epilogue -----"
popd
echo "----- END | Epilogue -----"

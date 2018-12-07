.. _docker-development:

Local Development in Docker
===========================

Note: The instructions here are **NOT** for production. They are strictly for local development.

* All ``docker-compose`` commands should be run from inside ``/path/to/clound-inquisitor/docker``.
* After following the `Initial Setup`_, you can bring the whole system up with ``docker-compose up -d``. 

Requirements
------------

* docker >= 17.12.0
* docker-compose >= 1.18.0
* Internet Access
* A smile

Containers
----------

* base: Used as the base for the API and Schedulers.  It never actually runs a service.
* db: Mysql database mounted on host locally ``127.0.0.1:3306:3306``.
* api: The API mounted on host locally ``127.0.0.1:5000:5000``.
* frontend: The frontend mounted on host locally ``127.0.0.1:3000:3000``
* scheduler: The standalone scheduler. No ports exposed.
* nginx: Acts as a proxy into the system mounted on host locally ``127.0.0.1:8080:80`` and ``127.0.0.1:8443:443``

Requirements
------------

* User in AWS has trust permission for Cloud Inquisitor ``InstanceProfile``. Setting this up can be found in the `QuickStart <./../quickstart.rst>`_
* Copy ``/path/to/cloud-inquisitor/docker/files/dev-backend-config.json.sample`` to ``/path/to/cloud-inquisitor/docker/files/dev-backend-config.json``
  * All full uppercase phrases need to be changed

AWS API Key Configuration
-------------------------
There are two ways to get AWS API keys into the container.

1. You can set the ``access_key`` and ``secret_key`` in ``dev-backend-config.json``. If using STS tokens, you need to provide the ``session_token`` as well.
2. Set ``access_key``, ``secret_key``, and ``session_token`` to ``null`` in ``dev-backend-config.json``. Then set environment variables ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``.  If using STS tokens, you need to also set ``AWS_SESSION_TOKEN``.
  

Initial Setup
-------------

1. Build all images: 

::

   docker-compose build

2. Start db:

::

   docker-compose up -d db

3. Setup database for Cloud Inquisitor and start the API server (The db server takes a few moments to start the first time you turn it on.  This command will fail if the db is not ready):

::

   docker-compose run base bash -c "source /env/bin/activate &&  cloud-inquisitor db upgrade"
   docker-compose up -d api

4. Retrieve your admin password:

::

   docker-compose logs api | grep admin

5. Start the frontend: 

::

   docker-compose up -d frontend

6. Start nginx:

::
   
   docker-compose up -d nginx

The frontend will now be available on https://localhost:8443

7. After starting nginx, log in with admin creds and add your AWS account through the UI

::

   Accounts -> Button on the bottom right corner -> "+" button -> Fill in form

After adding the account, configure the IAM Role you will use

::

   Config -> role_name

8. Start the standalone scheduler:

::

   docker-compose up -d scheduler


9. Log out of the admin account and log back in to see your results

Making Changes to the Cloud-Inquistor core
---------------------------

Do not make changes to the code running on the container; container storage is not persistent
when you do not mounting your local filesystem.
Instead make your changes on your local file system then run:

::

   docker-compose restart api
   docker-compose restart scheduler

As part of their startup, the API and Scheduler reinstall cloud-inquisitor and this will
propagate your changes

Making Changes to the frontend
---------------------------

Do not make changes to the code running on the container; container storage is not persistent
when you do not mounting your local filesystem.
Uncomment the ``volumes`` and the path for mounting the fontend.  The frontend setup in your
``docker-compose.yml`` should look similar to:

::

   frontend:
     build:
       context: ./../
       dockerfile: ./docker/frontend-Dockerfile
     ports:
       - "127.0.0.1:3000:3000"
     volumes: 
       - "./relative/path/to/cinq-frontend:/frontend"
      # Change the above path to cinq-frontend to fit your directory structure

This will mount your local frontend onto the container. The container automatically looks for
changes to the frontend code and will recompile the front end. This takes a few seconds since
gulp is rebuilding the entire frontend for us.
        
Making Changes to plugins
---------------------------

Do not make changes to the code running on the container; container storage is not persistent
when you do not mounting your local filesystem.
Mount your plugins on ``/plugins/plugin-name`` inside the container.  The setup in your
``docker-compose.yml`` should look similar to:

::

  api:
    image: cinq_base
    ports:
      - "127.0.0.1:5000:5000"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
    volumes:
      - "./files/dev-backend-config.json:/usr/local/etc/cloud-inquisitor/config.json"
      - "./files/logging.json:/usr/local/etc/cloud-inquisitor/logging.json"
      - "./../:/cloud-inquisitor"
      - "./../../cinq-auditor-iam:/plugins/cinq-auditor-iam"
      - "./../../cinq-auditor-example2:/plugins/cinq-auditor-example2"	
      # Change the above path to the plugin to fit your directory structure

    command: >
      bash -c " source /env/bin/activate;

      cd /cloud-inquisitor/backend
      && python setup.py clean --all install > /dev/null;

      if [ -d /plugins ]; then
         cd /plugins;
         for plugin in `ls /plugins`; do 
             (cd $$plugin && python3 setup.py clean --all install)
         done;
      fi

      && cloud-inquisitor runserver -h 0.0.0.0 -p 5000;"
    depends_on:
      - base
      - db

This will mount your local plugin onto the container. The container automatically looks for
plugins when it starts to and will install them to the virtual env. This takes a few seconds.

The easiest way to propagate the changes is to just restart the container:
::

    docker-compose restart api
    docker-compose restart scheduler

Limitations
-----------

* All communication between containers is HTTP
* nginx uses a self signed cert
* Do **NOT** use this in production. We have not hardened the containers. **Some processes may run as root**.
        
Tips
----

* All ``docker-compose`` commands should be run from inside ``/path/to/cloud-inquisitor/docker``.
* After following the [initial setup](#initial-setup), you can bring the whole system up with ``docker-compose up -d``. 
* By default, the database persists and the volume located at ``/path/to/cloud-inquisitor/docker/database``
* To stop all services run ``docker-compose down``
* To stop an individual service run ``docker-compose kill <db|api|scheduler|frontend|nginx>``
* To view logs run ``docker-compose logs``
    * You can view individual logs by running ``docker-compose logs <db|api|scheduler|frontend|nginx>``
    * You can follow the logs by adding the ``-f`` flag
* Don't forget to save your admin password
* Changing the ``docker-compose.yml`` ``commmand`` requires you to kill the container and bring it back up

###########################
Local Development in Docker
###########################

Note: The instructions here are **NOT** for production. They are strictly for local development.

* All ``docker-compose`` commands should be run from inside ``/path/to/clound-inquisitor/docker``.
* After following the `Initial Setup`_, you can bring the whole system up with ``docker-compose up -d``. 

============
Requirements
============
* docker >= 17.06.0
* docker-compose 
* Internet Access
* A smile

==========
Containers
==========
* db: Mysql database server with ``3306`` exposed to the Docker network and bound on the same port on host.
* api: The backend API with ``5000`` exposed to the Docker network and bound on the same port on host.
* frontend: The front end for Cloud Inquisitor with ``80`` exposed on the docker network and bound on port ``8000`` on host.
* scheduler: The standalone scheduler.

============
Requirements
============

* MySql server (provided in ``docker-compose``).
* User in AWS has trust permission for Cloud Inquisitor ``InstanceProfile``. Setting this up can be found in the `QuickStart <./../quickstart.rst>`_
* Copy ``/path/to/cloud-inquisitor/docker/dev-backend-config.py.sample`` to ``/path/to/cloud-inquisitor/docker/dev-backend-config.py``
* AWS API keys and AWS Instance Role ARN updated in ``/path/to/cloud-inquisitor/docker/dev-backend-config.py``.

=============
Initial Setup
=============
1. Build all images: 

::

    docker-compose build

2. Start db:

::

    docker-compose up -d db

3. Setup database for Cloud Inquisitor and start the API server (The db server takes a few moments to start the first time you turn it on.  This command will fail if the db is not ready):

::

    docker-compose run api bash -c "cd /cloudinquisitor && source env/bin/activate && python3 manage.py db upgrade && python3 manage.py setup --headless"
    docker-compose up -d api

4. Retrieve your admin password:

::

    docker-compose logs api

5. Start the frontend: 

::

    docker-compose up -d frontend

The front-end UI will be available on http://localhost:8000

6. After starting the front end, log in with admin creds and add your AWS account through the UI

::

    Accounts -> Button on the bottom right corner -> "+" button -> Fill in form

After adding the account, log out and log back in.

8. Start the standalone scheduler:

::

    docker-compose up -d scheduler

===========================
Making Changes to your Code
===========================

Do not make changes to the code running on the container; container storage is not persistent. 

Instead, run the following sets of commands to get your code changes into the containers:

::

    docker-compose down
    docker-compose build
    docker-compose up -d
        
===========
Limitations
===========

* Currently only HTTP is supported
* Do **NOT** use this in production. We have not hardened the containers. **Some proccesses still run as root**.
        
====
Tips
====

* All ``docker-compose`` commands should be run from inside ``/path/to/cloud-inquisitor/docker``.
* After following the [initial setup](#initial-setup), you can bring the whole system up with ``docker-compose up -d``. 
* By default, the database persists and the volume located at ``/path/to/cloud-inquisitor/docker/database``
* To stop all services run ``docker-compose down``
* To view logs run ``docker-compose logs``

  * You can view individual logs by running ``docker-compose logs <db|api|scheduler|frontend>``

* Rebuild all containers when making changes
* Don't forget to save your admin password

----------------------------
Example Workflow with Docker
----------------------------

The following assumes you've already completed the `Initial Setup`_.

1. Pull the latest code down
2. Create your branch
3. Make your changes to the code
4. Run::

    docker-compose down
    docker-compose build
    docker-compose up -d

5. Repeat steps 3 and 4 as needed

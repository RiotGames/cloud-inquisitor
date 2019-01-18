Additional Options
==================

Databases
---------

Cinq is currently designed to run with MySQL Version 5.7.17. We recommend you stick to this version.

If you do not wish to use a local MySQL DB that the Cinq install gives you, in your variables file, simply set the following in your variables before you run the packer build to disable
the install and setup of the local DB and point to the database you'd like to use ::

"app_setup_local_db":     "False"
"app_db_uri":             "mysql://<user>:<pass>@<hostname>:3306/<yourdb>"


Once the AMI is created and you've logged in you'll need to initialize the database. In order to do so execute the following commands ::

# source /path/to/pyenv/bin/activate
# export INQUISITOR_SETTINGS=/path/to/cinq-backend/settings/production.py
# cd /path/to/cinq-backend
# cloud-inquisitor db upgrade
# python3 manage.py setup --headless

You may receive some warnings but these commands should succeed. Then if you restart supervisor you should be good to go ::

# supervisorctl restart all

You can look in /path/to/cinq-backend/logs/ to see if you have any configuration errors.


KMS and UserData
----------------

You may not wish to keep database credentials in flat configuration files on the instance. You can KMS encrypt these variables and pass them to the Cinq instance
via AWS userdata. In your variables file use the following ::

"app_use_user_data":                       "True",
"app_kms_account_name":                    "aws-account-name",

When you launch the AMI packer created, you can encrypt the APP_DB_URI setting ::

$ aws kms encrypt --key-id arn:aws:kms:us-west-2:<account_id>:key/xxxxxxxx-74f8-4c0c-be86-a6173f2eeef9 --plaintext APP_DB_URI="mysql://<user>:<pass>@<hostname>:3306/<yourdb>"

It will return a response with a field of CipherTextBlob that you can paste into your UserData field when you launch the AMI.

To verify your Cinq instance is using KMS, your production settings in ``/path/to/cinq-backend/settings/production.py`` should contain: ::

 USE_USER_DATA = True
 KMS_ACCOUNT_NAME = '<account_name>'
 USER_DATA_URL = 'http://169.254.169.254/latest/user-data'



Authentication Systems
^^^^^^^^^^^^^^^^^^^^^^

Cinq supports built-in authentication system (default), as well as federation authentication with OneLogin IdP via SAML.
It's possible that other IdPs can be used but this has not been tested.

Edit your ``/path/to/cinq-backend/settings/settings.json`` file and provide the required values: ::

 # source /path/to/pyvenv/bin/activate
 # cd /path/to/cinq-backend
 # cloud-inquisitor auth -a OneLoginSAML
   cloud_inquisitor.plugins.commands.auth Disabled Local Authentication
   cloud_inquisitor.plugins.commands.auth Enabled OneLoginSAML

Verify that your configuration is correct and the active system ::

 # cloud-inquisitor auth -l

 cloud_inquisitor.plugins.commands.auth --- List of available auth systems ---
 cloud_inquisitor.plugins.commands.auth Local Authentication
 cloud_inquisitor.plugins.commands.auth OneLoginSAML (active)
 cloud_inquisitor.plugins.commands.auth --- End list of Auth Systems ---


To switch back to local Auth simply execute ::

# cloud-inquisitor auth -a "Local Authentication"


Additional Customization
------------------------

In the packer directory, the build.json contains other parameters that you can modify at your discretion.


Packer Settings
^^^^^^^^^^^^^^^

* ``aws_access_key`` - Access Key ID to use. Default: `AWS_ACCESS_KEY_ID` environment variable
* ``aws_secret_key`` - Secret Key ID to use. Default: `AWS_SECRET_ACCESS_KEY` environment variable
* ``ec2_vpc_id`` - ID of the VPC to launch the build instance into or default VPC if left blank. Default: `vpc-4a254c2f`
* ``ec2_subnet_id`` - ID of the subnet to launch the build instance into or default subnet if left blank. Default: `subnet-e7307482`
* ``ec2_source_ami`` - AMI to use as base image. Default: `ami-34d32354`
* ``ec2_region`` - EC2 Region to build AMI in. Default: `us-west-2`
* ``ec2_ssh_username`` - Username to SSH as for AMI builds. Default: `ubuntu`
* ``ec2_security_groups`` - Comma-separated list of EC2 Security Groups to apply to the instance on launch. Default: `sg-0c0aa368,sg-de1db4ba`
* ``ec2_instance_profile`` - Name of an IAM Instance profile to launch the instance with. Default: `CinqInstanceProfile`


Installer Settings
^^^^^^^^^^^^^^^^^^

* ``git_branch`` - Specify the branch to build Default: `master`
* ``tmp_base`` - Base folder for temporary files during installation, will be created if missing. Must be writable by the default ssh user. Default: `/tmp/packer`
* ``install_base`` - Base root folder to install to. Default: `/opt`
* ``pyenv_dir`` - Subdirectory for the Python virtualenv: Default : `pyenv`
* ``frontend_dir`` - Subdirectory of `install_base` for frontend code. Default: `cinq-frontend`
* ``backend_dir`` - Subdirectory of `install_base` for backend code. Default: `cinq-backend`
* ``app_apt_upgrade`` - Run `apt-get upgrade` as part of the build process. Default: `True`

Common Settings
^^^^^^^^^^^^^^^

* ``app_debug`` - Run Flask in debug mode. Default: `False`

Frontend Settings
^^^^^^^^^^^^^^^^^

* ``app_frontend_api_path`` - Absolute path for API location. Default: `/api/v1`
* ``app_frontend_login_url`` - Absolute path for SAML Login redirect URL. Default: `/saml/login`

Backend Settings
^^^^^^^^^^^^^^^^

* ``app_db_uri`` - **IMPORTANT:** Database connection URI. Example: ``mysql://cinq:changeme@localhost:3306/cinq``
* ``app_db_setup_local`` - This tells the builder to install and configure a local mysql database. Default - null
* ``app_db_user`` - Mysql username. Default  - null
* ``app_db_pw`` - Mysql password. Default - null
* ``app_api_host`` - Hostname of the API backend. Default: ``127.0.0.1``
* ``app_api_port`` - Port of the API backend. Default: ``5000``
* ``app_api_workers`` - Number of worker threads for API backend. Default: ``10``
* ``app_ssl_enabled`` - Enable SSL on frontend and backend. Default: ``True``
* ``app_ssl_cert_data`` - Base64 encoded SSL public key data, used if not using self-signed certificates. Default: ``None``
* ``app_ssl_key_data`` - Base64 encoded SSL private key data, used if not using self-signed certificates. Default: ``None``
* ``app_use_user_data`` - Tells Cinq to read variables from encrypted user-data
* ``app_kms_account_name`` - Provides an account name for kms.
* ``app_user_data_url`` - URL where user data is access. Default: ``http://169.254.169.254/latest/user-data``

FYI
^^^
The vast majority of these settings should be left at their default values unless you fell you must change them to get Cinq running.

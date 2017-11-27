***************************
Local Development in Packer
***************************

===============================================
Local Development - Starting cinq-backend
===============================================
Nginx should already be configured to serve the front-end and forward backend requests to flask.
(``cat /etc/nginx/sites-enabled/cinq.conf``)

You can run ``python3 manage.py`` to see a list of project tasks (e.g., runserver, db reload, auth config).

1. Start the Cloud Inquisitor *cinq* ``runserver`` target for development mode (auto-load python changes.) ``run_api_server`` is the production target.
::

    python3 manage.py runserver

2. Start scheduler to fetch aws data and other scheduled tasks.
::

    python3 manage.py run_scheduler

3. (Alternative) Run using supervisor.
::
   
    # service supervisor start
    # supervisorctl stop cinq cinq-scheduler
    # supervisorctl start cinq cinq-scheduler
  
4. Get generated local admin password.
::

    grep password: /opt/cinq-backend/logs/apiserver.log*

5. Browse to https://localhost.

If using a virtual machine, you may need to map ``127.0.0.1:443`` to the guest's port 443.
You may also need to manually browse to https://localhost/login.

===========================================================
Local Development - SSO and AWS Key Management Service
===========================================================
Local development configuration defaults to built in authentication. Further customization is required to work with features such as Single-Sign On (SSO) and AWS Key Management Services.

=================
Testing the build
=================

Once you have a successful AMI built you should launch a new EC2 Instance based off the AMI to ensure that everything was installed correctly.

* Launch **EC2** from within your AWS IAM Console & then select the AMI you have just created.

* Create from AMI

* As soon as the instance is up, connect to it via **ssh**.

* Check the status of the Cloud Inquisitor processes in ``supervisor`` by running `sudo supervisorctl`, which should return:

::

    bash
    # supervisorctl status
    cinq                   RUNNING    pid 4393, uptime 18 days, 18:55:44
    cinq-scheduler         RUNNING    pid 22707, uptime 13 days, 0:23:28

If both processes are not in the **RUNNING** state, then review the following:

* the ``/var/log/supervisor/cloudinquisitor*`` file for errors. There is most likely an issue in your JSON **variables** file, so you should do a direct comparison with the production */opt/cinq-backend/settings/production.py* file.
* the packer build output for errors (the **variables json** file can sometimes be the issue due to incorrect database details/credentials).

Once you have verified that both processes are running, you should terminate the scheduler since having multiple schedulers running at the same time can cause various issues. To do this from the shell:

*  ``supervisorctl stop cinq-scheduler``

or from within the _supervisorctl_ prompt

* ``supervisor> stop cinq-scheduler``

which results in:: bash supervisor> status
    cinq                   RUNNING    pid 1168, uptime 0:04:52
    cinq-scheduler         STOPPED    Oct 13 05:32 PM
    ```

Once you have verified that everything is running as expected you can terminate the EC2 Instance.

-------------------------------------------------------
AWS Deployment - AutoScalingGroup launch configurations
-------------------------------------------------------

Once you have tested that the image is good, update the Launch Configuration for the ASG following the steps below.

-----------------------------
Creating Launch Configuration
-----------------------------

1. Log into the AWS Console and go to the EC2 section.
2. Click ``Launch Configurations`` in the ``Auto Scaling`` section.
3. Locate the currently active Launch Configuration, right click it and choose ``Copy launch configuration``. To identify the currently active Launch Configuration you can look at the details for the Auto Scaling Group itself.
4. On the first screen, click ``Edit AMI`` and paste the AMI ID you got from the packer build (or search by ami name).
5. Once you select the new AMI, the console will ask you to confirm that you want to proceed with the new AMI, select ``Yes, I want to continue with this AMI`` and click Next.
6. On the instance type page, simply click ``Next: Configure details`` without modifying anything. The correct instance type will be pre-selected.
7. On the Details page you want to modify the Name attribute of the launch configuration. Name should follow the standard ``cloud-inquisitor-<year>-<month>-<day>_<index>`` with index being an increasing number that resets each day. So the first launch configuration for a specific day is _1. Ideally you shouldn't have to make multiple revisions in a single day, but this lets us easily revert to a previous version if we need to. You should ensure that the IAM role is correctly set to ``cloud-inquisitorInstanceProfile``.
8. After changing the launch configuration name, click the Next buttons until you reach the Review page. Make sure all the changes you made are reflected on the Review page and then hit ``Create launch configuration``. Once you click create it will ask you to select the key-pair, select an appropriate key-pair and click the Create button. Our base AMI have the InfraSec SSH keys baked into it, so you should not need to worry too much about the key-pair, but its still a good idea to use a key-pair the entire team has access to, just in case.

-------------------------
Updating AutoScalingGroup
-------------------------

1. Click on ``Auto Scaling Groups`` in the ``EC2 Dashboard``.
2. Locate the ASG you want to update, right click it and select ``Edit``.
3. From the ``Launch Configuration`` drop down box, locate the configuration you created in the previous step.
4. Click ``Save``.
5. With the ASG selected, click on the ``Instances`` tab in the details pane. 
6. Click on the instance ID to be taken to the details page for the EC2 instance.
7. Right click EC2 Instance and select terminate. This will trigger the ASG to launch a new instance from the updated launch configuration on the new AMI. This process takens 3-5 minutes during which time ``Cloud Inquisitor`` will be unavailable.
8. Go back to the ASG details page for the Cloud Inquisitor ASG, and by clicking the Refresh icon monitor that a new instance is being launched and goes into ``InService`` status. Once the new instance is in service, verify that you are able to log into the UI at ``https://cloudinquisitor.<your_domain>/`` or whatever the relevant URL is.

--------------------------------------
Connect to new instance and upgrade DB
--------------------------------------
::

    ssh -i <ssh key> ubuntu@<instance ip>
    sudo supervisorctl stop all
    cd /opt/cloudinquisitor-backend/
    export CINQ_SETTINGS=/opt/cinq-backend/settings/production.py
    sudo -u www-data -E python3 manage.py db upgrade
    sudo -u www-data -E python3 manage.py setup --headless
    sudo supervisorctl start all
    # You can review the logs in /var/log/inquisitor-backend/logs
    # Browse to the Cloud Inquisitor UI and update the config to enable new features.

NOTE: THIS STUFF IS IN DEVELOPMENT. DO NOT USE

# Introduction
The software is intended for installation on an internet connected Ubuntu server that can be configured to allow incoming network requests.  Although this guide details all the steps necessary to get the service running on a public DNS it should not be considered complete or safe.  Running a safe, secure, robust internet connected service is way beyond the scope of this document.  It is assumed the end user of this software has the expertise necessary to operate the software and assumes all risk consequent to it's operation.

# Install nginx

   - Follow steps 1 and 2 at [How to install nginx on Ubunut 18](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04)

# Install Pre-Requisite Components

   - ```sudo apt update```
   - ```sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools```

# Install fopdw

This procedure is based upon the information found [here](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04).

## Clone the fopdw Code
   - ```git clone https://github.com/ferguman/fopdw```

## Create Python 3 Virtual Environment for your local instance of fopdw
   - ```sudo apt install python3-venv```
   - ```cd ~/fopdw```
   - ```python3 -m venv fopdw```

## Install Python Libraries

   - ```source ./fopdw/bin/activate```
   - ```pip install wheel```
   - ```pip install -r requirements.txt``` 

# Configure fopdw

## Private Key File

   - ```cp config/private_key_template.py config/private_key.py```

   - Open the private_key.py file and refer to the comments in the source code for instructions on how to populate the various values that are stored in this file.

## Configuration File

   - ```cp config/config_template.py config/config.py

   - Edit the config.py file and refer to the comments in the source code for instructions on how to populate the various configuration values that are stored in this file.

## Test Flask

  - ```python fopdw``` - This will run the Flask application at 0.0.0.0:8081.  Note you can change the port by editing the fopdw.py file.

# Configure Gunicorn and nginx

## Gunicorn

Note: The fopdw code base includes a file named wsgi.py that is inteaded to be the WSGI entry point.  You should modify the file to suite your server environment needs.

   -Test your Gunicorn install by running ```gunicorn --bind 0.0.0.0:8081 wsgi:app```.

   -You should now be able to browse localhost:8080 and see the logon page for fopdw.

   -Close the Gunicorn session created above.

   -```sudo vim /lib/systemd/system/fopdcw_gunicorn.service``` - create an empty service file.

   -Edit the file created above and configure it to be the service file for the fopdw Gunicorn service. You
can use this [template](https://github.com/ferguman/fopdw/blob/master/docs/gunicorn_service_file).

   -```sudo systemctl start fopdcw_gunicorn.service``` - start the Gunicorn service

   -```sudo systemctl status fopdcw_gunicorn.service``` - check that the service is running ok

   -```sudo systemctl enable fopdcw_gunicorn.service``` - enable the Gunicorn service to start everytime the system is booted.

## nginx

We will configure nginx to proxy the Gunicorn service created in the steps above.
      
   - Create a new file /etc/nginx/sites-available/fopdw. Use this [template](https://github.com/ferguman/fopdw/blob/master/docs/fopd_nginx_file) for your new file and modify to fit your environment.
      
   - ```sudo ln -s /etc/nginx/sites-available/fopdw /etc/nginx/sites-enabled/fopdw``` - creates a symbolic link to the file created in the step above. The link is created in the sites-enabled directory which triggers nginx to enable the site.

   -```sudo nginx -t``` - this command will test the configure file to make sure it looks good to nginx.

   -```sudo systemctl restart nginx``` - restart nginx to take up the new configuration file.

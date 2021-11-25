# codecamp-portail-entreprise
Welcome to this test API aimed to provide a backend and DB for Qovoltis "portail entreprise" codecamp.  

**What is it ?**

This API is build with flask python micro-framework for REST APIs. It takes its data from a 
Sqlite3 database.

# Installation

**Requirements**

To run the API you will need on your machine : 
- python>=3.7 : https://www.python.org/downloads/
- according to your python version you may need to install manually pip (https://pypi.org/project/pip/) and virtualenv (https://pypi.org/project/virtualenv/)
- sqlite3 : https://www.sqlite.org/index.html


**Configuration**

The directory where you downloaded or pulled the code will be referred as {appDir}. 
Ex /home/my-user/codeCampQovoltis

**1)**
Create in a place of your convenience a directory for storing the api data and logs. 
It will be referred as {appDataDir}, ex /home/my-user/codeCampQovoltisData. Inside this directory
create a subdirectory files and logs

**2)**
In {appDir} copy the hidden file .env.dist to a new file .env and edit it to set the variables
*LOG_FILEPATH* and ** :
LOG_FILEPATH={appDataDir}/logs, ex /home/my-user/codeCampQovoltisData/logs
DATA_FILEPATH={appDataDir}/files, ex /home/my-user/codeCampQovoltisData/files 

**3)**
In {appDir}/sql are the scripts db_creation.sql for initializing api DB and db_drop.sql for dropping all tables 
and data. 
Create your db with the command : 

*sqlite3 {appDataDir}/files/db.sqlite < {appData}/sql/db_creation.sql* 

Ex : *sqlite3 /home/my-user/codeCampQovoltisData/files/db.sqlite < /home/my-user/codeCampQovoltis/sql/db_creation.sql*

To check if the creation was successful you can explore the db with 

*sqlite3 {appDataDir}/files/db.sqlite* 

then type

*SELECT * from address;*

You should get : 
1|2A rue Danton|1|48.8182737|2.3292709...

**4)**
For all the following your current directory must be {appDir}.

create the virtual environment for running the project with command : 

*python3 -m venv ./venv*

After that you should see in {appDir} the new subdirectory venv.

**5)**
Activate the venv with the command

*source venv/bin/activate*

After activation each terminal line should be prefixed with (venv)

Install the project requirements by typing : 

*pip install -r requirements.txt*

You should get a final message of this kind : Successfully installed Flask-1.1.2 Flask-Cors-3.0.10...

You can now exit the virtualenv by typing :

*deactivate*

**Congratulations !**
**your installation is now complete ! You're ready to launch the test API.**

# Launch

Go to current directory {appDir} and activate the venv first (see configuration.5).

*python3 main.py*

You can now browse to http://127.0.0.1:8000 , you should get the default page of the api. 

You can also change default port (8000) and default host (127.0.0.1) by launching with parameters : 

*python3 main.py --host=0.0.0.0 --port=7999*

**Test users**

For using the api you need to login first. 
Default db already comes with two organizations (QOvoltis and Etna) and a lot of test users : 

Qovoltis users : 

administrator@dummy.qovoltis.com (administrator)
ellen.willis@dummy.qovoltis.com
alan.fleming@dummy.qovoltis.com
larry.baker@dummy.qovoltis.com
samantha.hicks@dummy.qovoltis.com
carrie.holahan@dummy.qovoltis.com
june.roderiquez@dummy.qovoltis.com

Etna users

administrator@dummy.etna.com (administrator)
sandra.pawlak@dummy.etna.com
nicholas.hamilton@dummy.etna.com
mark.frahm@dummy.etna.com
edwin.daniels@dummy.etna.com
gary.remaley@dummy.etna.com
byron.rodriguez@dummy.etna.com


Users authenticate with their email and password *password* by default. 


# Postman Documentation



# Contact

In case of problem with the API you can send a mail to **simon.thuillier@qovoltis.com**.





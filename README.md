# Amazon Mechanical Turk (AMT) codebase for the QueryVis User Study 
Some code structure and workflow was adapted from https://github.com/akuznets0v/quickstart-mturk and https://github.com/akuznets0v/mturk-lean-external-question which provide a nice template for deploying a simple AMT test with Heroku and Flask.

# Remarks
Notice that some fields such as: `DATABASE_URL`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` need to be specified accordingly when setting up the postgres database on heroku and using AWS keys with MTURK.

# Mturk Quick Setup
* Register on mturk.com and https://requester.mturk.com/developer/sandbox
* Deploy to heroku by commiting and pushing the repository with `git push heroku master`.
* Run `post_hits.py` to post the hits on Amazon Mechanical Turk
* Amazon Mechanical Turk will post your HIT, and IFrame your url in when a user accepts it.
* Once a user completes the hit it will be logged in the database. For more options check the hit_manager.py

# Useful Commands

## Local testing of Flask server


Using Ubuntu straight or via WSL:


https://code.visualstudio.com/docs/remote/wsl

```code .``` from wsl

```sudo apt-get update```
```sudo apt-get upgrade```

### upgrade python
```sudo apt-get install software-properties-common```
```sudo add-apt-repository ppa:deadsnakes/ppa```
```sudo apt update```
```sudo apt install python3.11-full```
```sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2```
And choose which one to use as Python3 via the command:
```sudo update-alternatives --config python3```

```sudo apt-get install python3.11-dev```


```sudo apt-get install postgresql postgresql-contrib```

Optional:
``` sudo apt-get install pgadmin3```

--- pgadmin https://stackoverflow.com/questions/45707319/pgadmin-on-windows-10-with-postgres-when-installed-via-bash-on-ubuntu-on-windows


posting in case someone had my issue

In my case I was getting Connection refused, I was able to resolve by changing listen_addresses property to '*' inside postgresql.conf file

To locate conf file on ubuntu

sudo -u postgres psql -c 'SHOW config_file'
once you find the file, you need to change listen_addresses like this

listen_addresses = '*'
Then restart postgres using

sudo service postgresql restart
you might need to change the permission of the file before you can edit it, don't forget to revert this change once done.

---


```sudo passwd postgres```

it56uZ

See status with ```service postgresql status```

```sudo service postgresql start```


```sudo -u postgres psql```
Inside the `psql` shell 

```ALTER USER postgres PASSWORD 'newPassword';```

In bash
```export DATABASE_URL="postgresql://flask:j89zD*@localhost:5432/rdstudy"```

```export AWS_ACCESS_KEY_ID="AKIATFTO66IA5EM4HJLS"```
```export AWS_SECRET_ACCESS_KEY="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"```
```export FLASK_SECRET_KEY="d469f8ee47e65fbf3b2eef2fdadb63807981d1e052a94fbc"```

```
>>> import os
>>> os.urandom(24)
'\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'
>>> print(os.urandom(24).hex())
```


```CREATE DATABASE rdstudy;```

```\l```

```CREATE USER flask WITH PASSWORD 'j89zD*';```
```GRANT ALL PRIVILEGES ON DATABASE rdstudy to flask;```

```sudo apt-get install libssl-dev```

```python3 -m venv env```

```source env/bin/activate```

```pip3 install wheel```

```pip3 install -r requirements.txt```


Set environment variables using a `.env` file. The file should contain:
```
FLASK_DEBUG=True
FLASK_APP=rd_study_server.py
LOCAL=True
TESTING=True
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
FLASK_SECRET_KEY=
LOCAL_SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/rdstudy
SQLALCHEMY_TRACK_MODIFICATIONS=False
```



On Windows with WSL, install https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack


```python db_create.py```
Actually, this only currently works with debugpy from VSCode... Why?


``` sudo -u postgres psql -d rdstudy```

in postgres

```\dt``` shows you the tables and ```SELECT * FROM USERS;``` shows you an empty table with columns.



```bash
flask run
```

http://127.0.0.1:5000/?workerId=a&assignmentId=b&hitId=c
https://rd-study.herokuapp.com?workerId=a&assignmentId=b&hitId=c

## Deploying on Heroku

Create a pipeline on Heroku that will create from GitHub.

Locally:

```cmd
heroku plugins:install heroku-config
heroku login
```
to switch to our app
```cmd
heroku domains -a rd-study
```
where `rd-study` is the app name on Heroku

```cmd
heroku open -a rd-study
heroku config:push --file=.env.production -a rd-study
```


## Basic/useful Postgres psql commands
To connect in psql as user aristotle: `sudo -u aristotle psql postgres`\
To check information about current connection from psql: `\conninfo`\
Drop a database: `dropdb 'database name'`\
\
Give user create database rights
```
su postgres
psql
alter user aristotle createdb;
```
Check the database in heroku: `heroku pg:psql`\
Delete all data from a table: `Truncate Table;`

## Performing migration
To initialize the process: `python manage.py db init`\
\
To perform a migration locally
```
python manage.py db migrate
python manage.py db upgrade
```
\
To perform a migration on heroku on our server:
```
heroku run python manage.py db migrate --app afternoon-waters-70012
heroku run python manage.py db upgrade --app afternoon-waters-70012
```
Then login into heroku and drop the table `users` and run `db_create.py` to re-create it based on the updated schema.\
\
Copying a local database to heroku: `heroku pg:push postgresql:///queryvis heroku_database_name`

## Heroku useful commands
Login to heroku server
```
heroku login
heroku run bash
```
\
Get config variables: `heroku config --app afternoon-waters-70012`\
\
To add the postgres user to the sudo group: `sudo usermod -a -G sudo postgres`\
\
Run script on heroku: `heroku run python script.py`\
\
Dump database content in a CSV file: `\copy (SELECT * from users) TO dump.csv CSV DELIMITER ',' CSV HEADER`

## Useful online SQL/Text/Image formatters/converters
SQL to HTML: http://hilite.me/ \
SQL to HTML: https://htmlcodeeditor.com/ \
Removes non-ascii characters: https://pteo.paranoiaworks.mobi/diacriticsremover/ \
PDF to PNG: https://pdf2png.com/
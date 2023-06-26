# Amazon Mechanical Turk (AMT) codebase for the Relational Diagrams User Study<!-- omit in toc -->

Code and instructions for running the Relational Diagrams MTurk User Study using Heroku & Postgres.

* [Remarks](#remarks)
* [MTurk Quick Setup](#mturk-quick-setup)
* [Useful Commands](#useful-commands)
  * [Local testing of Flask server](#local-testing-of-flask-server)
    * [Setup for using Ubuntu via WSL](#setup-for-using-ubuntu-via-wsl)
    * [Setup using Ubuntu](#setup-using-ubuntu)
  * [Deploying on Heroku](#deploying-on-heroku)
* [Instructions for dealing with AMT interactions](#instructions-for-dealing-with-amt-interactions)
  * [AWS / AMT setup](#aws--amt-setup)
  * [Setup](#setup)
  * [`create_qualification.py`](#create_qualificationpy)
  * [`post_hits.py`](#post_hitspy)
  * [`hit_manager.py`](#hit_managerpy)
  * [`approve_hits.py`](#approve_hitspy)
* [Old](#old)
  * [Basic/useful Postgres psql commands](#basicuseful-postgres-psql-commands)
  * [Performing migration](#performing-migration)
  * [Heroku useful commands](#heroku-useful-commands)
  * [Useful online SQL/Text/Image formatters/converters](#useful-online-sqltextimage-formattersconverters)



# Remarks

Notice that some fields such as: `DATABASE_URL`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` need to be specified accordingly when setting up the postgres database on heroku and using AWS keys with MTURK.

# MTurk Quick Setup

- Register on mturk.com and <https://requester.mturk.com/developer/sandbox>
- Deploy to heroku by commiting and pushing the repository with `git push heroku master`.
- Run `post_hits.py` to post the hits on Amazon Mechanical Turk
- Amazon Mechanical Turk will post your HIT, and IFrame your url in when a user accepts it.
- Once a user completes the hit it will be logged in the database. For more options check the hit_manager.py

# Useful Commands

## Local testing of Flask server

### Setup for using Ubuntu via WSL

1. Update WSL

   ```ps
   wsl --update
   ```

2. Install Unbuntu from the Windows store so that it keeps up to date.
3. With VSCode open from Windows, install <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack>
4. Within WSL Bash, run VSCode from the folder with:

   ```bash
   code .
   ```

   (See <https://code.visualstudio.com/docs/remote/wsl> for details.)

### Setup using Ubuntu

1. Upgrade packages:

   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. Upgrade Python to 3.11 (necessary for Heroku deployment)

    ```bash
    sudo apt install software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.11-full python3.11-dev python3.11-venv gcc
    python3.11 -m ensurepip
   ```

   !Danger! Don't do the following unless you want to risk breaking your terminal! But it does let you set the default `python3` to be `python3.11`

   ```bash
   sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2
   ```

   And choose which one to use as Python3 via the command:

   ```bash
   sudo update-alternatives --config python3
   ```

3. Install postgres (and libssl-dev)

    ```bash
    sudo apt install postgresql postgresql-contrib libssl-dev 
    ```

    1. Optional: Install pgadmin for managing the DB:

        1. If using WSL, install on Windows by downloading from <https://www.pgadmin.org/download/pgadmin-4-windows/>. See details at <https://stackoverflow.com/questions/45707319/pgadmin-on-windows-10-with-postgres-when-installed-via-bash-on-ubuntu-on-windows>

        2. If pure Ubuntu:

            ```bash
            sudo apt install pgadmin4
            ```

    2. Set a postgres Ubuntu user password:

        ```bash
        sudo passwd postgres
        ```

        E.g., `it56uZ`.

    3. Set a postgres database user password:

        ```bash
        sudo -u postgres psql
        ```

        Inside the `psql` shell set the password. Make sure to set your own value for `newPassword` before running:

        ```sql
        ALTER USER postgres PASSWORD 'newPassword';
        ```

    4. Set up the postgres databases and user for the app. Still in the `psql` shell:

        1. Create the database and list the ones present.

            ```sql
            CREATE DATABASE rdstudy;
            \l
            ```

        2. Then, create the user `flask`. Make sure to set your own value for `newPassword` before running:

            ```sql
            CREATE USER flask WITH PASSWORD 'newPassword';
            GRANT ALL PRIVILEGES ON DATABASE rdstudy to flask;
            ```

        3. Exit `psql` by running:

            ```sql
            \q
            ```

    5. See status with

        ```bash
        service postgresql status
        ```

    6. Start the server with

        ```bash
        sudo service postgresql start
        ```

    7. To avoid getting connection refused errors, edit the `postgresql.conf` file.

        1. Locate the conf file:

            ```bash
            sudo -u postgres psql -c 'SHOW config_file'
            ```

        2. Edit the file. E.g.:

            ```bash
            sudo nano /etc/postgresql/14/main/postgresql.conf
            ```

        3. In the file, uncomment `listen_addresses` and change it like so:

            ```ini
            listen_addresses = '*'
            ```

        4. Then restart postgres using

            ```bash
            sudo service postgresql restart
            ```

4. Create a `.env` file that holds your environmental variables.
    1. Generate a `FLASK_SECRET_KEY`, e.g., running this in the Python intepreter:

        ```python
        import os
        os.urandom(24)
        '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'
        print(os.urandom(24).hex())
        ```

    2. Then fill out the `.env` file something like this, ensuring that you fill in the values for `XXXXX` below. Use:

        1. `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from <https://requestersandbox.mturk.com/developer> for the Sandbox or <https://requester.mturk.com/developer> for live deployment.
        2. The `FLASK_SECRET_KEY` you generated
        3. The password you set for the postgres `flask` account as part of `LOCAL_SQLALCHEMY_DATABASE_URI`.

        ```ini
        FLASK_DEBUG=True
        FLASK_APP=rd_study_server.py
        LOCAL=True
        TESTING=True
        AWS_SANDBOX=True
        AWS_ACCESS_KEY_ID=XXXXX
        AWS_SECRET_ACCESS_KEY=XXXXX
        AWS_CHECK_QUAL=True
        AWS_ALLOW_QUAL_ERROR=True
        FLASK_SECRET_KEY=XXXXX
        LOCAL_SQLALCHEMY_DATABASE_URI=postgresql://flask:XXXXX@localhost:5432/rdstudy
        SQLALCHEMY_TRACK_MODIFICATIONS=False
        WEB_CONCURRENCY=2
        ```

5. Install Python requirements in a virtual environment.

    1. Install wheel for building packages and ensure `libpq-fe.h` is available from libpq-dev:

        ```bash
        python3.11 -m pip install wheel
        sudo apt-get install --reinstall libpq-dev
        ```

    2. Create the virtual environment:

        ```bash
        sudo python3.11 -m venv env
        source env/bin/activate
        ```

    3. Install wheel and then the requirements:

        ```bash
        python3.11 -m pip install -r requirements.txt
        ```



Run `db_create.py` to populate the database. This currently only works with running debugging from VSCode..., i.e., `debugpy`. It is unclear why...

`sudo -u postgres psql -d rdstudy`

in postgres

`\dt` shows you the tables and `SELECT * FROM USERS;` shows you an empty table with columns.

```bash
flask run
```

<http://127.0.0.1:5000/?workerId=AA&assignmentId=BB&hitId=CC>

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

to overwrite existing values, use

```cmd
heroku config:push --file=.env.production -a rd-study -o
```

```cmd
heroku run bash --app rd-study
python3 db_create.py
```

test gunicorn
`gunicorn --preload  rd_study_server:app --log-file - --log-level=debug`

<http://127.0.0.1:8000/?workerId=AA&assignmentId=BB&hitId=CC>

<https://rd-study.herokuapp.com?workerId=AA&assignmentId=BB&hitId=CC>

For testing AMT

```
heroku config:push --file=.env.sandbox -a rd-study -o
heroku ps:restart -a rd-study
```

For live AMT

```
heroku config:push --file=.env.live -a rd-study -o
heroku ps:restart -a rd-study
```

papertrail logging (paid)

```cmd
heroku addons:create papertrail:fixa
```

Access through Heroku site

To see the database with, e.g., PGAdmin, get the value of `DATABASE_URL` on Heroku:

```cmd
heroku config:get DATABASE_URL -a rd-study
```

It is of the form

```
postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

Set under Connection:

- Hostname/address: `HOST`
- Port: `PORT`
- Maintenance database: `DATABASE`
- Username: `USERNAME`
- Password: `PASSWORD`

Set under Advanced:

- DB restriction: `DATABASE`

Click Save

Navigate to the database > Schemas > public > Tables > users.
Right-click and select View/Edit Data > All Rows.

postgres://bksmptywmdqgrw:736cca0ed9a698081223b023492213fa779e21a3fcf0c86ad2c362c09802d992@ec2-52-21-136-176.compute-1.amazonaws.com:5432/d29vcdcg0m1mv4

# Instructions for dealing with AMT interactions

## AWS / AMT setup

Create your AWS account and an associated AMT account.

## Setup

1. Ensure your environment variables are set. You can use a line like this to load one of the environment files into environment variables, in this case `.env.sandbox.text`:

```bash
set -o allexport && source .env.sandbox.test && set +o allexport
```
**Note!** All your `.env` files need to have LF and not CRLF line endings for this to work properly. Otherwise, you'll get errors like 
`botocore.exceptions.HTTPClientError: An HTTP Client raised an unhandled exception: Invalid header value`. You can check this with, e.g., `cat -t .env.sandbox.text`.

You can check variables with `printenv | grep AWS`.

## `create_qualification.py`
Creates a qualification using questions from `qualification_questions.xml` and answers from `qualification_answers.xml`. 
Uses the `AWS_SANDBOX`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` environment variables.
**!!!WARNING!!!** hard-coded text for the qualification details! Make sure to at least change the `Name` and hard-coded bits in [`post_hits.py`](./post_hits.py).
Run in the terminal. Pass in one of these arguments:

* `test`: Creates the basic qualification.
* `custom`: Creates a custom qualification for invited workers only, e.g,. those who had errors taking the test.
* `test_taken`: Creates a test taken qualification to eliminate workers who have taken the test previously.

E.g., inside the virtual environment you'll need to run both:

```
python ./create_qualification.py test
python ./create_qualification.py test_taken
```

Record the `QualificationId`s to use in [`post_hits.py`](./post_hits.py) for the `qualification_id` and `taken_test_qualification_id` variables.

If you get a `RequestError` about having a `QualificationType` with this name already, you need to change the **hard-coded `Name=`** part of the file or delete the existing qualification at 
<https://requestersandbox.mturk.com/qualification_types> or <https://requester.mturk.com/qualification_types>.

## `post_hits.py`
Creates a HIT. Uses the `AWS_SANDBOX`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` environment variables.
**!!!WARNING!!!** hard-coded text!

**!!!WARNING!!!** The HITs you create programmatically here [***Do Not*** show up on the web management interface](https://stackoverflow.com/questions/50382623/hits-created-with-create-hit-with-externalquestion-using-boto3-not-visible-at-r)! Amazon has deprecated that feature—aargh! 

1. Update the `<ExternalURL>` tag in [`external_question.xml`](./external_question.xml) to be the URL of your Heroku app.
2. Update all these **hard-coded elements** in [`post_hits.py`](./post_hits.py) (some docs on [AMT docs](https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_CreateHITOperation.html)), and read the file! 

   1. `qualification_id`: The basic qualification.
   2. `custom_qualification_id`: A custom qualification for invited workers.
   3. `taken_test_qualification_id`: A test taken qualification to eliminate workers who took the test previously.
   4. `base_pay`: The lowest level of reward.
   5. `approval_percentage`
   6. `minimum_qualification_score`
   7. `title_str`
   8. `description-str`
   9. `MaxAssignments`
   10. `LifetimeInSeconds`
   11. `AssignmentDurationInSeconds`

Run in inside the virtual environment with one of these arguments:
* `full`: Regular full-duration HIT.
* `pilot`: Shorter pilot HIT.
* `custom WID QID`: Post a custom hit for worker with ID `WID` who has been given a custom qualification with ID `QID`.

E.g., 

```
python ./post_hits.py full
```



## `hit_manager.py`
Has lots of code for various things. Make sure to read the code before running it! Run in the terminal. Pass in one of these arguments followed by parameters:

* `summary`: Provides a summary of the last 100 hits
* `clear`: Deletes all HITs except the ones in a **!!!WARNING!!!** hard-coded `except_list`. Will auto-reject all assignments pending in the HIT!
* `extend NUM`: Add `NUM` more assignments. **!!!WARNING!!!** hard-coded `hit_id`.
* `hit_detail HID`: Get details inc. showing a graph for HIT with ID `HID`.
* `hits_detail HID1 HID2`: Get details for two HIT IDs.
* `get_assignments HID STATUS`: Get assignments for HIT ID `HID` with status `STATUS` one of `['Approved', 'Rejected', 'Submitted']`.
* `get_worker_id_list HID`: Get worker IDs for HIT with ID `HID` that are Approved or Rejected.
* `approve_qualifications QID`: Approve qualifications for qualification ID `QID`. **!!!WARNING!!!** hard-coded `accept_list` in `approve_qualifications` definition.
* `update_expiration HID`: Update the expiration for HIT ID `HID`. **!!!WARNING!!!** hard-coded `ExpireAt` in `update_expiration` definition.
* `give_worker_qualification QID WID`: Give qualification with ID `QID` to worker with ID `WID`.
* `set_taken_test_qualification QID WFILE`: Read worker IDs from `WFILE` which has one ID per line and **ADD** to each worker the qualification with ID `QID`.
* `remove_qualification QID WFILE`: Read worker IDs from `WFILE` which has one ID per line and **REMOVE** from each worker the qualification with ID `QID`.
* `get_workers_with_qualification QID`: List the workers with qualification ID `QID`.
* `get_qualification_score QID WID`: Get the qualification score on qualification with ID `QID` for worker with ID `WID`.
* `notify_workers_with_qualification QFILE TFILE`: Notify all workers listed in the qualified workers file `QFILE` (one ID per line) that are in the file of workers that haven't taken the HIT `TFILE` (one ID per line). **!!!WARNING!!!** Hard-coded advertisement message.

## `approve_hits.py`

1. Depends on the `REMOTE_DATABASE_URI` environment variable being set to point to the Heroku Postges Database. Note: This will change regularly! There are two ways to get this value:
   1. Access through Heroku site, e.g., https://dashboard.heroku.com/apps/rd-study/settings
   2. Use the Heroku CLI:

        ```cmd
        heroku config:get DATABASE_URL -a rd-study
        ```

    It is of the form

    ```
    postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE
    ```


# Old

## Basic/useful Postgres psql commands

To connect in psql as user cody: `sudo -u cody psql postgres`\
To check information about current connection from psql: `\conninfo`\
Drop a database: `dropdb 'database name'`\
\
Give user create database rights

```
su postgres
psql
alter user cody createdb;
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
Copying a local database to heroku: `heroku pg:push postgresql:///rd heroku_database_name`

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

SQL to HTML: <http://hilite.me/> \
SQL to HTML: <https://htmlcodeeditor.com/> \
Removes non-ascii characters: <https://pteo.paranoiaworks.mobi/diacriticsremover/> \
PDF to PNG: <https://pdf2png.com/>
# MTurk codebase for the study "SQL vs. Visual Diagrams on time and correctness matching relational query patterns"<!-- omit in toc -->

Code and instructions for running the study "SQL vs. Visual Diagrams on time and correctness matching relational query patterns" using Amazon Mechanical Turk (MTurk), Heroku, and Postgres.

- [Remarks](#remarks)
- [MTurk Initial Setup and Overview](#mturk-initial-setup-and-overview)
- [Useful Commands](#useful-commands)
  - [Local testing of Flask server](#local-testing-of-flask-server)
    - [Setup for using Ubuntu via WSL](#setup-for-using-ubuntu-via-wsl)
    - [Setup using Ubuntu](#setup-using-ubuntu)
  - [Deploying on Heroku](#deploying-on-heroku)
  - [Possible `.env` files](#possible-env-files)
- [Instructions for dealing with MTurk interactions](#instructions-for-dealing-with-mturk-interactions)
  - [AWS / MTurk setup](#aws--mturk-setup)
  - [Setup](#setup)
  - [`create_qualification.py`](#create_qualificationpy)
  - [`post_hits.py`](#post_hitspy)
  - [`hit_manager.py`](#hit_managerpy)
  - [`approve_hits.py`](#approve_hitspy)

# Remarks

Notice that some fields such as: `DATABASE_URL`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` need to be specified accordingly when setting up the Postgres database on Heroku and using AWS keys with MTurk.

**!!Warning!!** Tutorial time is not currently captured correctly due to a database bug.

# MTurk Initial Setup and Overview

- Register on <https://requester.mturk.com/> for deployment and <https://requester.mturk.com/developer/sandbox> for testing.
- Deploy to Heroku by committing and pushing the repository with `git push heroku master.`
- Run `post_hits.py` to post the hits on Amazon Mechanical Turk
- Amazon Mechanical Turk will post your HIT, and IFrame your URL when a user accepts it.
- Once a user completes the HIT it will be logged in the database. For more options, check the hit_manager.py

# Useful Commands

## Local testing of Flask server

### Setup for using Ubuntu via WSL

1. Update WSL

   ```ps
   wsl --update
   ```

2. Install Unbuntu from the Windows store to keep it current.
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

3. Install Postgres (and libssl-dev)

   ```bash
   sudo apt install postgresql postgresql-contrib libssl-dev
   ```

   1. Optional: Install pgadmin for managing the DB:

      1. If using WSL, install on Windows by downloading from [pgadmin.org](https://www.pgadmin.org/download/pgadmin-4-windows/). See details at [StackOverflow](https://stackoverflow.com/questions/45707319/pgadmin-on-windows-10-with-postgres-when-installed-via-bash-on-ubuntu-on-windows).

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

      Inside the `psql` shell, set the password. Make sure to set your own value for `NEWPASSWORD` before running:

      ```sql
      ALTER USER postgres PASSWORD 'NEWPASSWORD';
      ```

   4. Set up the postgres databases and user for the app. Still in the `psql` shell:

      1. Create the database and list the ones present.

         ```sql
         CREATE DATABASE rdstudy;
         \l
         ```

      2. Then, create the user `flask`. Make sure to set your own value for `NEWPASSWORD` before running:

         ```sql
         CREATE USER flask WITH PASSWORD 'NEWPASSWORD';
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

   1. Generate a `FLASK_SECRET_KEY`, e.g., running this in the Python interpreter:

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

To view the running site, use, for example: <http://127.0.0.1:5000/?workerId=AA&assignmentId=BB&hitId=CC>

## Deploying on Heroku

Create a pipeline on Heroku that will be created from GitHub.

Locally:

```cmd
heroku plugins:install heroku-config
heroku login
```

to switch to our app

```cmd
heroku domains -a rd-study
```

where `rd-study` is the app name on Heroku.

This opens the website:

```cmd
heroku open -a rd-study

```

To overwrite existing values, use

```cmd
heroku config:push --file=.env.live -a rd-study -o
```

**Warning:** This fails silently if the file doesn't exist.

**make sure to log in fresh to the latest deployment**, then:

```cmd
heroku run bash --app rd-study
python3 db_create.py
```

You can test it with gunicorn like so:

```cmd
gunicorn --preload  rd_study_server:app --log-file - --log-level=debug
```

To view the running site, use, for example:

- Local: <http://127.0.0.1:8000/?workerId=AA&assignmentId=BB&hitId=CC>
- Live <https://rd-study.herokuapp.com?workerId=AA&assignmentId=BB&hitId=CC>

For testing MTurk

```
heroku config:push --file=.env.sandbox -a rd-study -o
heroku ps:restart -a rd-study
```

For live MTurk

```
heroku config:push --file=.env.live -a rd-study -o
heroku ps:restart -a rd-study
```

Papertrail logging (paid)—Note that this plan has a 65MB/day limit which you can easily exceed even running 60 participants. We recommended you use a higher plan.

```cmd
heroku addons:create papertrail:fixa
```

To export logs, you can use the scripts found in [`/logs/papertrail`](/logs/papertrail/).

Access Papertrail through the Heroku site.

To see the database with, e.g., PGAdmin:

1. Get the value of `DATABASE_URL` on Heroku:

   ```cmd
   heroku config:get DATABASE_URL -a rd-study
   ```

   It is of the form

   ```
   postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE
   ```

2. Set under Connection:

   - Hostname/address: `HOST`
   - Port: `PORT`
   - Maintenance database: `DATABASE`
   - Username: `USERNAME`
   - Password: `PASSWORD`

3. Set under Advanced:

   - DB restriction: `DATABASE`

4. Click Save.
5. Navigate to the database > Schemas > public > Tables > users.
   Right-click and select View/Edit Data > All Rows.

## Possible `.env` files

Here are some options you can create:

- [.env.local.sandbox](.env.local.sandbox) for local development and sandbox grading
- [.env.local.live](.env.local.live) for local development and MTurk live grading
- [.env.sandbox.test](.env.sandbox.test) to use for testing the MTurk Sandbox site.
- [.env.sandbox](.env.sandbox) for more production-ready testing on the MTurk Sandbox site. Turns off error display to users and requires qualifications.
- [.env.live.test](.env.live.test) to use for the live MTurk website.
- [.env.live](.env.live) to use for the live MTurk website. Turns off error display to users and requires qualifications.

# Instructions for dealing with MTurk interactions

## AWS / MTurk setup

Create your AWS account and an associated MTurk account.

## Setup

1. Ensure your environment variables are set. You can use a line like this to load one of the environment files into environment variables, in this case `.env.sandbox.text`:

```bash
set -o allexport && source .env.sandbox.test && set +o allexport
```

likewise, for the actual grading of the submitted HITs:

```bash
set -o allexport && source .env.live && set +o allexport
```

**Note!** All your `.env` files need to have LF and not CRLF line endings for this to work properly. Otherwise, you'll get errors like
`botocore.exceptions.HTTPClientError: An HTTP Client raised an unhandled exception: Invalid header value`. You can check this with, e.g., `cat -t .env.sandbox.text`.

You can check variables in general with `printenv | grep AWS`.

## `create_qualification.py`

Creates a qualification using questions from `qualification_questions.xml` and answers from `qualification_answers.xml`.
Uses the `AWS_SANDBOX`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` environment variables.
**!!!WARNING!!!** hard-coded text for the qualification details! Make sure to at least change the `Name` and hard-coded bits in [`post_hits.py`](./post_hits.py).
Run in the terminal. Pass in one of these arguments:

- `test`: Creates the basic qualification.
- `custom`: Creates a custom qualification for invited workers only, e.g., those who had errors taking the test.
- `test_taken`: Creates a test taken qualification to eliminate workers who have taken the test previously.

E.g., inside the virtual environment, you'll need to run both:

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

**!!!WARNING!!!** The HITs you create programmatically here [**_Do Not_** show up on the web management interface](https://stackoverflow.com/questions/50382623/hits-created-with-create-hit-with-externalquestion-using-boto3-not-visible-at-r)! Amazon has deprecated that feature—aargh!

1. Update the `<ExternalURL>` tag in [`external_question.xml`](./external_question.xml) to be the URL of your Heroku app.
2. Update all these **hard-coded elements** in [`post_hits.py`](./post_hits.py) (some docs on [MTurk docs](https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_CreateHITOperation.html)), and read the file!

   1. `qualification_id`: The basic qualification.
   2. `custom_qualification_id`: A custom qualification for invited workers.
   3. `taken_test_qualification_id`: A test taken qualification to eliminate workers who previously took the test.
   4. `base_pay`: The lowest level of reward.
   5. `approval_percentage`
   6. `minimum_qualification_score`
   7. `title_str`
   8. `description-str`
   9. `MaxAssignments`
   10. `LifetimeInSeconds`
   11. `AssignmentDurationInSeconds`

Run inside the virtual environment with one of these arguments:

- `full`: Regular full-duration HIT.
- `pilot`: Shorter pilot HIT.
- `custom WID QID`: Post a custom hit for the worker with ID `WID` who has been given a custom qualification with ID `QID`.

E.g.,

```
python ./post_hits.py full
```

## `hit_manager.py`

Has lots of code for various things. Make sure to read the code before running it! Run in the terminal. Pass in one of these arguments followed by parameters:

- `summary`: Provides a summary of the last 100 hits

**!!!Warning!!!** Everything below needs to be checked to see if it needs a paginator added to handle more than 100 records.

- `balance`: Gets current prepaid HIT balance.
- `clear`: Deletes all HITs except the ones in a **!!!WARNING!!!** hard-coded `except_list`. Will auto-reject all assignments pending in the HIT!
- `extend NUM`: Add `NUM` more assignments. **!!!WARNING!!!** hard-coded `hit_id`.
- `hits_detail HID1 HID2`: Get details for two HIT IDs.
- `get_assignments HID STATUS`: Get assignments for HIT ID `HID` with status `STATUS` one of `['Approved', 'Rejected', 'Submitted']`.
- `get_worker_id_list HID`: Get worker IDs for HIT with ID `HID` that are Approved or Rejected.
- `approve_qualifications QID`: Approve qualifications for qualification ID `QID`. **!!!WARNING!!!** hard-coded `accept_list` in `approve_qualifications` definition.
- `update_expiration HID`: Update the expiration for HIT ID `HID`. **!!!WARNING!!!** hard-coded `ExpireAt` in `update_expiration` definition.
- `give_worker_qualification QID WID`: Give qualification with ID `QID` to worker with ID `WID`.
- `set_taken_test_qualification QID WFILE`: Read worker IDs from `WFILE` which has one ID per line and **ADD** to each worker the qualification with ID `QID`.
- `remove_qualification QID WFILE`: Read worker IDs from `WFILE` which has one ID per line and **REMOVE** from each worker the qualification with ID `QID`.
- `get_workers_with_qualification QID`: List the workers with qualification ID `QID`.
- `get_qualification_score QID WID`: Get the qualification score on qualification with ID `QID` for worker with ID `WID`.
- `notify_workers_with_qualification QFILE TFILE`: Notify all workers listed in the qualified workers file `QFILE` (one ID per line) that are in the file of workers that haven't taken the HIT `TFILE` (one ID per line). **!!!WARNING!!!** Hard-coded advertisement message.

## `approve_hits.py`

Deals with submissions.

**!!!Warning!!!** Hard-coded messages to workers here, including the `reject_message` variable.

Depends on the `REMOTE_DATABASE_URI` environment variable being set to point to the Heroku Postges Database. Note: This will change regularly! There are two ways to get this value:

1.  Access through Heroku site, e.g., https://dashboard.heroku.com/apps/rd-study/settings
2.  Use the Heroku CLI:

    ```cmd
    heroku config:get DATABASE_URL -a rd-study
    ```


    It is of the form

    ```
    postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE
    ```

Ensure the environment variables are set. E.g., for live payment:

```
set -o allexport && source .env.local.live && set +o allexport
```

**!!!Warning** currently these claim to update the DB saying who was paid but do not actually. Use the contents of the [/logs](/logs) folder to check status.

Pass in one of these arguments:

- `batch_grade HID`: Check Submitted assignments for a given HIT ID and Approve them.
- `batch_grade_test HID`: Check Submitted assignments for a given HIT ID and Approve them.
- `send_manual_bonus WID AID`: Send a bonus to a given worker ID for given assignment ID (because we accepted but didn't send a bonus the first time.)
- `reject AID FEEDBACK`: Reject the given assignment ID with a given feedback. E.g., rejecting speeders.
- `approve AID`: Approve the given assignment ID like normal.
- `grade AID WID`: Grade and approve hits as necessary for a given assignment ID and worker ID

E.g., using your `HID`:

```
python ./approve_hits.py batch_grade HID
```

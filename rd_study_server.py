from __future__ import division
from models import *
from models import db
import math
import os
# import boto3
import json
import datetime
import random
from enum import Enum
from flask import Flask, render_template, url_for, request, make_response, request, send_from_directory, redirect  # jsonify, session
from flask_sqlalchemy import SQLAlchemy
# from flask_heroku import Heroku
from post_hits import get_connection, qualification_id
from logging.config import dictConfig

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": "flask.log",
                "when": "D",
                "interval": 10,
                "backupCount": 60,
                "formatter": "default",
            },
        },
        "root": {"level": "INFO", "handlers": ["console", 'file']},
    }
)

app = Flask(__name__, static_url_path='')

app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# This allows us to specify whether we are pushing to the sandbox or live site.
if os.environ.get('TESTING'):
    AMAZON_HOST = "https://workersandbox.mturk.com/mturk/externalSubmit"
else:
    AMAZON_HOST = "https://www.mturk.com/mturk/externalSubmit"

# # Set up SQLAlchemy variables and settings
if (os.environ.get('LOCAL')):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'LOCAL_SQLALCHEMY_DATABASE_URI')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'REMOTE_SQLALCHEMY_DATABASE_URI')

db.init_app(app)
db.app = app

SECTION_FOLLOWER = {
    Sections.INSTRUCTIONS: Sections.TUTORIAL,
    Sections.TUTORIAL: Sections.TEST,
    Sections.TEST: Sections.RESULTS
}

# Configuration for returning workers
returning_workers_filename = 'data/worker_ids_taken_old_hit.csv'
returning_workers_sequence_num_amount = [0, 0, 0, 0, 0, 0]

# Creates the questions dictionary that includes the choices (a-d) for each of the 12 questions

NUM_QUESTIONS = 32
NUM_PATTERNS = 4
NUM_MODES = 2

MIN_NUM_CORRECT_QUESTIONS = 16
MIN_ALLOWED_ACCURACY = 0.5
MAX_ALLOWED_TIME_SEC = 50*60  # in seconds


def create_questions_array():
    import json

    # returns JSON object as
    # a dictionary
    allQuestionData = json.load(open('data/questions.json'))
    usedQuestionData = allQuestionData[1:33]

    if NUM_QUESTIONS != len(usedQuestionData):
        pass  # XXXXXXXXX XXX
        # raise Exception('Expected ', NUM_QUESTIONS, ' questions, file had ', len(questionData))

    choices = ["a", "b", "c", "d"]  # For each of the NUM_PATTERNS

    # Iterating through the json
    # list
    # for questionDatum in questionData:
    #     sqlpattern1 = questionDatum['sqlpattern1']
    #     sqlpattern2 = questionDatum['sqlpattern2']
    #     sqlpattern3 = questionDatum['sqlpattern3']
    #     sqlpattern4 = questionDatum['sqlpattern4']
    #     diagrampattern1 = questionDatum['diagrampattern1']
    #     diagrampattern2 = questionDatum['diagrampattern2']
    #     diagrampattern3 = questionDatum['diagrampattern3']
    #     diagrampattern4 = questionDatum['diagrampattern4']
    #     answer1 = questionDatum['answer1']
    #     answer2 = questionDatum['answer2']
    #     answer3 = questionDatum['answer3']
    #     answer4 = questionDatum['answer4']
    #     questions[questions_key]

    return usedQuestionData


def getPatternOrder():
    sequence_length = NUM_PATTERNS * NUM_MODES * 2
    if (NUM_QUESTIONS % sequence_length) != 0:
        raise Exception(
            NUM_QUESTIONS + ' is not evenly divisible by  ' + sequence_length)
    num_sequences = math.floor(NUM_QUESTIONS / sequence_length)

    pattern_order = []
    for sequence in range(1, num_sequences+1):
        temp_order = []
        for i in [1, 2]:  # To go along with the *2 multiplier above
            for pattern in range(1, NUM_PATTERNS+1):
                for mode in range(1, NUM_MODES+1):
                    temp_order.append(pattern)
        random.shuffle(temp_order)
        pattern_order.extend(temp_order)
    return pattern_order

# Creates the answers dictionary that includes the letter answer (a-d) for each of the 12 questions


def create_answers_dict():
    answers_json = open('static/questions/answers.json')
    answer_str = answers_json.read()
    answers = json.loads(answer_str)
    return answers

# Returns a sequence number for a given worker. The sequence number is assigned
# so that the sizes of the different sequence number groups are balanced
# It also tries to balance groups when assigning returning workers


def assign_sequence_num(worker_id):
    # Read the returning workers
    with open(returning_workers_filename) as f:
        returning_workers = f.readlines()
    returning_workers = [x.strip() for x in returning_workers]

    # check if current worker is a returning worker
    if worker_id in returning_workers:
        app.logger.info('worker_id ' + worker_id + ' is a returning worker')
        lowest_sequence_num_amount = returning_workers_sequence_num_amount.index(
            min(returning_workers_sequence_num_amount))
    else:
        sequence_num_amount = []
        # sequence_num = "sequence_num"
        for i in range(2):
            amount = db.session.query(User.sequence_num).filter_by(
                sequence_num=i).count()
            sequence_num_amount.append(amount)
            app.logger.info('There are ' + str(amount) +
                            ' users with sequence_num = ' + str(i))

        lowest_sequence_num_amount = sequence_num_amount.index(
            min(sequence_num_amount))

    app.logger.info("The sequence_num with the lowest assigned workers is: " +
                    str(lowest_sequence_num_amount))

    # Set sequence_num in the database
    user = db.session.query(User).filter_by(worker_id=worker_id).one()
    user.sequence_num = lowest_sequence_num_amount
    user.pattern_order = getPatternOrder()
    app.logger.info('User assigned pattern order ' + str(user.pattern_order))
    db.session.commit()

    return lowest_sequence_num_amount


def getUser(request, createUser):  # createUser says optionally create if necessary
    worker_id = request.args.get("workerId")
    hit_id = request.args.get("hitId")
    assignment_id = request.args.get("assignmentId")
    full_path = request.full_path

    app.logger.info(logString([
        "Request full path:", full_path,
        "for worker_id:", worker_id,
        "assignment_id:", assignment_id,
        "hit_id:", hit_id
    ]))

    if worker_id == None or assignment_id == None or hit_id == None:
        app.logger.error(
            'Insufficient arguments provided in full path: ' + full_path)
        raise Exception(
            'Insufficient arguments provided in full path: ' + full_path)

    if assignment_id == "ASSIGNMENT_ID_NOT_AVAILABLE":
        raise Exception('Preview assignment but not preview code?!')

    # Check if user exists with the same worker_id in the database
    exists = db.session.query(User).filter_by(worker_id=worker_id).scalar()

    user = None

    # if (os.environ.get('LOCAL')):
    #     worker_id = "TEST"
    #     assignment_id = "TEST"
    #     hit_id = "TEST"

    if exists:
        app.logger.info("Detected EXISTING worker_id " + str(worker_id))
        # we don't check createUser as it is optional

        # Query user from DB
        user = db.session.query(User).filter_by(worker_id=worker_id).one()

        # check arguments match DB
        if user.assignment_id != assignment_id:
            app.logger.warn('worker_id ' + worker_id + "'s assignment_id in DB (" +
                            user.assignment_id + ") doesn't match provided id (" + assignment_id + ')')
        if user.hit_id != hit_id:
            app.logger.warn('worker_id ' + worker_id + "'s hit_id in DB (" +
                            user.hit_id + ") doesn't match provided id (" + hit_id + ')')
    else:
        if createUser:
            # Add the new user into the database
            app.logger.info(
                'Creating NEW user for worker_id ' + str(worker_id))
            user = User(worker_id=worker_id,
                        assignment_id=assignment_id, hit_id=hit_id)

            # Grab the user's qualification score and place it in the database
            if (not os.environ.get('LOCAL')):
                conn = get_connection()
                response = conn.get_qualification_score(
                    QualificationTypeId=qualification_id,
                    WorkerId=user.worker_id
                )
                qualification_score = response['Qualification']['IntegerValue']
                user.qualification_score = qualification_score

            user.current_section = Sections.INSTRUCTIONS
            user.current_page = 1

            # Record the datetime a new user is added
            start_datetime = datetime.datetime.utcnow()
            user.start_datetime = start_datetime
            app.logger.info(logString([
                'worker_id', str(worker_id),
                'starting datetime in UTC was', str(user.start_datetime)
            ]))

            db.session.add(user)
            db.session.commit()
        else:
            msg = 'Unable to find user for worker_id ' + \
                worker_id + ' but we were not told to create user.'
            app.logger.error(msg)
            raise Exception(msg)

    return user


def updateProgressAndGetRedirect(user, current_section, next_section):
    redirect_route = None

    if next_section:
        proper_next_section = SECTION_FOLLOWER[user.current_section]
        if current_section != proper_next_section:
            # For some reason there is a weird issue where 2 requests are made from tutorial
            if current_section != Sections.TUTORIAL:
                app.logger.error('full_path ' + request.full_path + ' asked for section ' +
                                 current_section.name + ' but proper next section was ' + proper_next_section.name)
        else:
            user.current_section = current_section
            user.current_page = 1
            db.session.commit()

    if user.current_section == current_section:
        return None
    elif user.current_section == Sections.INSTRUCTIONS:
        redirect_route = 'main'
    elif user.current_section == Sections.TUTORIAL:
        redirect_route = 'tutorial'
    elif user.current_section == Sections.TEST:
        redirect_route = 'test'
    elif user.current_section == Sections.RESULTS:
        redirect_route = 'results'
    else:
        raise Exception('Undefined section for worker_id ' +
                        user.worker_id + ': ' + user.current_section)

    return redirect(
        url_for(
            redirect_route,
            workerId=user.worker_id,
            assignmentId=user.assignment_id,
            hitId=user.hit_id,
            currentPage=user.current_page))


def logString(input_array):
    return ' '.join(str(s) for s in input_array)


# ---------------------------------------------- ROUTES ----------------------------------------------#
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/', methods=['GET', 'POST'])
def main():
    preview = False

    # Check if the worker clicked on preview. If so, skip creating user
    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        app.logger.info(
            "Worker has clicked to preview the task with request full_path " + request.full_path)
        preview = True
        resp = make_response(render_template(
            "instructions.hAtml", preview=preview))
        resp.headers['x-frame-options'] = '*'
        return resp

    user = getUser(request=request, createUser=True)

    possibleRedirect = updateProgressAndGetRedirect(
        user, Sections.INSTRUCTIONS, request.args.get('nextSection'))
    if possibleRedirect:
        return possibleRedirect

    app.logger.info(logString([
        "worker_id", user.worker_id,
        "had a qualification score of", str(user.qualification_score)
    ]))

    resp = make_response(
        render_template(
            "instructions.html",
            preview=False,
            worker_id=user.worker_id,
            assignment_id=user.assignment_id,
            hit_id=user.hit_id))

    # This is particularly nasty gotcha.
    # Without this header, your iFrame will not render in Amazon
    resp.headers['x-frame-options'] = '*'
    return resp


@app.route('/tutorial', methods=['GET', 'POST'])
def tutorial():
    user = getUser(request=request, createUser=False)

    possibleRedirect = updateProgressAndGetRedirect(
        user, Sections.TUTORIAL, request.args.get('nextSection'))
    if possibleRedirect:
        return possibleRedirect

    resp = make_response(
        render_template(
            "tutorial.html",
            worker_id=user.worker_id,
            assignment_id=user.assignment_id,
            hit_id=user.hit_id,
            current_page=user.current_page))
    resp.headers['x-frame-options'] = '*'
    return resp


@app.route('/tutorial_record_time', methods=['GET', 'POST'])
def tutorialClick():
    if request.method == 'POST':
        data = json.loads(request.form['data'])

        # Get the data
        tutorial_page_num = data['tutorial_page_num']
        current_page = data['current_page']
        # Insecure, but we don't really care about tutorial time
        time_spent = data['time_spent']
        worker_id = data['worker_id']

        app.logger.info("Worker: " + worker_id + " moved away from tutorial page " + str(tutorial_page_num) +
                        ", elapsed time increased by " + str(time_spent))

        # Get the user
        user = db.session.query(User).filter_by(worker_id=worker_id).one()

        # Apply the changes to the database
        tutorial_time = getattr(user, "tutorial_time")
        if (tutorial_time == None):
            tutorial_time = time_spent
        else:
            tutorial_time += time_spent

        setattr(user, "tutorial_time", tutorial_time)
        setattr(user, 'current_page', current_page)
        db.session.commit()

        app.logger.info('worker_id ' + worker_id +
                        'Set tutorial_time to ' + str(tutorial_time))

    if request.method == 'GET':
        app.logger.info(
            "Wrong request, tutorial_record_time request should be POST not GET")

    return "OK"


# actual route used for questions
@app.route('/test', methods=['GET', 'POST'])
def test():
    user = getUser(request=request, createUser=False)

    possibleRedirect = updateProgressAndGetRedirect(
        user, Sections.TEST, request.args.get('nextSection'))
    if possibleRedirect:
        return possibleRedirect

    # Create dictionary for the questions and answers data
    app.questions = create_questions_array()

    current_time = datetime.datetime.utcnow()

    start_time = user.q1_start  # should only happen first question
    if start_time == None:
        start_time = current_time

    max_end_time = start_time + \
        datetime.timedelta(seconds=MAX_ALLOWED_TIME_SEC)

    time_remaining_delta = max_end_time - current_time
    time_remaining_ms = int(time_remaining_delta.total_seconds() * 1000)

    resp = make_response(
        render_template(
            "test.html",
            worker_id=user.worker_id,
            assignment_id=user.assignment_id,
            hit_id=user.hit_id,
            current_page=user.current_page,
            time_remaining_ms=time_remaining_ms,
            questions=app.questions))
    resp.headers['x-frame-options'] = '*'
    return resp


@app.route('/record_choice_get_answer', methods=['POST'])
def record_choice_get_answer():
    app.logger.info("record_choice_get_answer called with " +
                    request.method + " request")
    if request.method == 'POST':
        data = request.json
        question_num = data['question_num']
        worker_id = data['worker_id']

        app.logger.info(logString([
            "worker_id", worker_id,
            "reporting choice for question", question_num
        ]))

        user = db.session.query(User).filter_by(worker_id=worker_id).one()

        sql_question_column = 'q' + str(question_num)
        question_start_col = sql_question_column + "_start"
        question_end_col = sql_question_column + "_end"
        question_time_col = sql_question_column + "_time"
        user_choice = data['user_choice']

        # Can't just use exceptions as the user needs something in case in broken state
        invalid = False
        if user[sql_question_column] != None or user[question_end_col] != None or user[question_time_col] != None:
            app.logger.warning('Unexpected setting question end time and answer again. worker_id ' +
                               str(worker_id) + ', question ' + str(question_num))
            invalid = True

        if user[question_start_col] == None:
            app.logger.warning(
                'Tried to set question time for a question that has not been started.')
            invalid = True

        question_end = datetime.datetime.utcnow()
        question_time = question_end - user[question_start_col]
        question_time_ms = int(question_time.total_seconds() * 1000)

        if not invalid:
            setattr(user, sql_question_column, user_choice)
            setattr(user, question_end_col, question_end)

            setattr(user, question_time_col, question_time_ms)
            db.session.commit()

        # Our questions start at 1, our index starts at 0
        pattern_num = user.pattern_order[question_num - 1]
        question = app.questions[question_num - 1]

        answer_key = 'answer' + str(pattern_num)
        answer_text = question[answer_key]

        ret_data = {
            'answerNum': pattern_num,
            'answerText': answer_text
        }

        correct_string = '(Correct)'
        if pattern_num != user_choice:
            correct_string = '(Incorrect, correct was ' + \
                str(pattern_num) + ')'

        app.logger.info(logString([
            'worker_id', worker_id,
            'for question', question_num,
            'chose answer', user_choice,
            correct_string,
            'at', question_end,
            'Took', question_time_ms/1000, 'seconds.',
            'Answer text', answer_text]
        ))

        return ret_data

    if request.method == 'GET':
        app.logger.info(
            "Wrong request, record_choice_get_answer request should be POST not GET")

    return "OK"


# Modifies the database in order to record a user's question choice and time spent on that question
@app.route('/get_next_question', methods=['POST'])
def get_next_question():
    app.logger.info("get_next_question called with " +
                    request.method + " request")
    if request.method == 'POST':
        question_num = request.json['question_num']
        worker_id = request.json['worker_id']
        app.logger.info(logString([
            "worker_id", str(worker_id),
            " requesting next question, question_num ", str(question_num)
        ]))

        user = db.session.query(User).filter_by(worker_id=worker_id).one()

        sequence_num = user.sequence_num

        # Our questions start at 1, our index starts at 0
        pattern_num = user.pattern_order[question_num - 1]
        question = app.questions[question_num - 1]

        # example of question format is
        # {
        #     table1: 'Employee',
        #     table2: 'Works_on',
        #     table3: 'Project',
        #     table1alias: 'E',
        #     table2alias: 'W',
        #     table3alias: 'Part',
        #     attribute11: 'lname',
        #     attribute12: 'ssn',
        #     attribute21: 'pno',
        #     attribute22: 'essn',
        #     attribute31: 'pnumber',
        #     diagrampattern1: 'nnlmukzedmco',
        #     diagrampattern2: 'qozjhjhfdusl',
        #     diagrampattern3: 'bbgujydyzkar',
        #     diagrampattern4: 'xxddfftxepbx',
        #     sqlpattern1: 'gkfprksqvzon',
        #     sqlpattern2: 'gfgnnctuuylq',
        #     sqlpattern3: 'zdynbjjdvvjh',
        #     sqlpattern4: 'lszvknnnqxcn',
        #     answer1: 'Find employees who work on **some** project.',
        #     answer2: 'Find employees who do **not** work on **any** project.',
        #     answer3: 'Find employees who do **not** work on **all** projects.',
        #     answer4: 'Find employees who work on **all** projects.',
        # }

        # question_num is [1,2,3,4,5...32]
        # sequence_num is [0, 1]
        # 0 & 1 SQL
        # 0 & 2 RD
        # 0 & 3 SQL

        # 1 & 1 RD
        # 1 & 2 SQL
        # 1 & 3 RD

        image_key_base = ''
        if sequence_num > 1:
            raise Exception(
                'Unhandled image location definition for sequence num ' + sequence_num)
        elif (sequence_num + question_num) % 2 == 1:
            image_key_base = 'sqlpattern'
        elif (sequence_num + question_num) % 2 == 0:
            image_key_base = 'diagrampattern'
        else:
            raise Exception('Unhandled image location definition for sequence num ' +
                            sequence_num + ' question_num ' + question_num)
        image_key = image_key_base + str(pattern_num)

        ret_data = {
            'image': question[image_key] + '.svg',
            'answerStrings': [
                question['answer1'],
                question['answer2'],
                question['answer3'],
                question['answer4']
            ]
        }

        sql_question_column = 'q' + str(question_num)
        question_start_col = sql_question_column + "_start"
        question_end_col = sql_question_column + "_end"
        question_time_col = sql_question_column + "_time"

        question_start = datetime.datetime.utcnow()
        if user[question_start_col] != None or user[sql_question_column] != None or user[question_end_col] != None or user[question_time_col] != None:
            app.logger.error(logString([
                'Unexpected setting start question time again. worker_id', worker_id,
                'question_num ', question_num
            ]))
        else:

            setattr(user, question_start_col, question_start)
            setattr(user, 'current_page', question_num)
            db.session.commit()

        app.logger.info(logString([
            'worker_id', worker_id,
            'started question num', question_num,
            'at', question_start,
            '. Sending question details:', ret_data
        ]))

        return ret_data

    if request.method == 'GET':
        app.logger.info("Wrong request, request should be POST not GET")

    return "OK"


@app.route('/assign_sequence_num', methods=['GET', 'POST'])
def assign_sequence_num_route():
    '''
    Mode 1: Show SQL
    Mode 2: Show RD

    Sequence 0: 1,2,1,2,1,2...
    Sequence 1: 2,1,2,1,2,1...
    '''
    # TODO: use get_qualification_score (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html#MTurk.Client.get_qualification_score)
    # if we want to set the mode based on user performance in the qualification test

    worker_id = request.json['worker_id']
    app.logger.info(
        "assign_sequence_num route called for worker_id " + worker_id)

    user = db.session.query(User).filter_by(worker_id=worker_id).one()
    user.current_section = Sections.TUTORIAL
    db.session.commit

    sequence_num = user.sequence_num
    if (sequence_num == None):
        sequence_num = assign_sequence_num(worker_id)
        app.logger.info('worker_id ' + worker_id +
                        ' does not have a sequence number assigned, assigning them ' + str(sequence_num))
    return str(sequence_num)


# @app.route('/demographics', methods=['GET', 'POST'])
# def demographics():
#     print("Demographics route called")

#     resp = make_response(render_template("demographics.html"))
#     resp.headers['x-frame-options'] = '*'
#     return resp


# @app.route('/demographics_submit', methods=['POST'])
# def demographics_submit():
#     print("Demographics submit route called")
#     if request.method == 'POST':
#         data = json.loads(request.form['data'])
#         print(data)

#         # Get the data
#         likert_q1 = data['likert_q1']
#         likert_q2 = data['likert_q2']
#         likert_q3 = data['likert_q3']
#         likert_q4 = data['likert_q4']
#         likert_q5 = data['likert_q5']
#         likert_q6 = data['likert_q6']

#         feedback = data['feedback']
#         country = data['country']
#         gender = data['gender']
#         age = custom_to_int(data['age'])
#         occupation = data['occupation']
#         income = custom_to_int(data['income'])
#         sql_exp = data['sql_exp']
#         frequency = custom_to_int(data['frequency'])
#         usage = data['usage']

#         # Get the user
#         worker_id = data['worker_id']
#         user = db.session.query(User).filter_by(worker_id=worker_id).one()

#         # Apply the changes to the database
#         user.feedback = feedback
#         user.country = country
#         user.gender = gender
#         user.occupation = occupation
#         user.sql_exp = sql_exp
#         user.usage = usage

#         # Make sure we don't insert empty strings for integer columns
#         if (likert_q1 != ''):
#             user.likert_q1 = likert_q1
#         if (likert_q2 != ''):
#             user.likert_q2 = likert_q2
#         if (likert_q3 != ''):
#             user.likert_q3 = likert_q3
#         if (likert_q4 != ''):
#             user.likert_q4 = likert_q4
#         if (likert_q5 != ''):
#             user.likert_q5 = likert_q5
#         if (likert_q6 != ''):
#             user.likert_q6 = likert_q6

#         if (age != ''):
#             user.age = age
#         if (income != ''):
#             user.income = income
#         if (frequency != ''):
#             user.frequency = frequency

#         db.session.commit()

#     if request.method == 'GET':
#         print("Wrong request, request should be POST not GET")

#     return "OK"

# val is either an empty string or an integer string, custom_to_int converts the string to an integer if it wasn't empty


def custom_to_int(val):
    if (val == ''):
        return val
    else:
        return int(val)


@app.route('/results', methods=['GET', 'POST'])
def results():
    user = getUser(request=request, createUser=False)

    possibleRedirect = updateProgressAndGetRedirect(
        user, Sections.RESULTS, request.args.get('nextSection'))
    if possibleRedirect:
        return possibleRedirect

    # Record the datetime the user finishes
    end_datetime = datetime.datetime.utcnow()
    app.logger.info('worker_id ' + str(user.worker_id) +
                    ' finished. Ending datetime: ' + str(end_datetime))
    user.end_datetime = end_datetime
    db.session.commit()

    num_correct = 0

    total_question_time = 0
    total_timedelta = user.q32_end - user.q1_start
    total_time = int(total_timedelta.total_seconds() * 1000)

    for question_num in range(1, NUM_QUESTIONS + 1):
        q_col = "q" + str(question_num)
        q_time_col = "q" + str(question_num) + "_time"

        user_time = getattr(user, q_time_col)
        user_choice = getattr(user, q_col)
        # Our questions start at 1, our index starts at 0
        pattern_num = user.pattern_order[question_num - 1]

        if user_choice == pattern_num:
            num_correct += 1
            app.logger.info('worker_id ' + str(user.worker_id) +
                            ' has correct answer for question ' + str(question_num))
        else:
            app.logger.info('worker_id ' + str(user.worker_id) +
                            ' has wrong answer for question ' + str(question_num))

        total_question_time += user_time

    percentage_correct = num_correct / NUM_QUESTIONS
    app.logger.info("Number of correct answers is: " + str(num_correct))
    app.logger.info("Percentage of correct answers is " +
                    str(percentage_correct))
    app.logger.info('worker_id ' + str(user.worker_id) + "'s total time taken to complete the test is " + str("%.2f" %
                    (total_time / (1000 * 60))) + " minutes, but time on questions was " + str("%.2f" % (total_question_time / (1000 * 60))))

    accept = True
    failure_reason = ""

    # check if we will accept the hit
    if (num_correct < MIN_NUM_CORRECT_QUESTIONS):
        accept = False
        failure_reason = "you failed to answer " + \
            str(MIN_NUM_CORRECT_QUESTIONS) + " or more questions correctly."
    if (total_time > MAX_ALLOWED_TIME_SEC * 1000):
        accept = False
        failure_reason = "you failed to answer all questions within " + \
            str(MAX_ALLOWED_TIME_SEC/60) + " minutes."

    app.logger.info('worker_id ' + str(user.worker_id) +
                    " The hit acceptance is: " + str(accept))

    # TODO: Do not hard code variables
    # Calculate the bonus
    BASE_PAY = 5.00
    bonus_time = 0
    bonus_correctness = 0
    total_bonus = 0
    CORRECTNESS_PER_QUESTION_BONUS = 1.04

    # Calculate bonuses only if we accept the hit and submit the bonus
    if (accept):
        bonus_correctness = round((
            (num_correct - MIN_NUM_CORRECT_QUESTIONS) *
            CORRECTNESS_PER_QUESTION_BONUS if (num_correct - MIN_NUM_CORRECT_QUESTIONS > 0) else 0),
            2)

        if total_time < 8 * 60 * 1000:
            bonus_time = 0.35 * (BASE_PAY + bonus_correctness)
        elif total_time < 9 * 60 * 1000:
            bonus_time = 0.30 * (BASE_PAY + bonus_correctness)
        elif total_time < 10 * 60 * 1000:
            bonus_time = 0.25 * (BASE_PAY + bonus_correctness)
        elif total_time < 11 * 60 * 1000:
            bonus_time = 0.20 * (BASE_PAY + bonus_correctness)
        elif total_time < 12 * 60 * 1000:
            bonus_time = 0.15 * (BASE_PAY + bonus_correctness)
        elif total_time < 13 * 60 * 1000:
            bonus_time = 0.10 * (BASE_PAY + bonus_correctness)
        elif total_time < 14 * 60 * 1000:
            bonus_time = 0.05 * (BASE_PAY + bonus_correctness)
        bonus_time = round(bonus_time, 2)

        app.logger.info("Bonus from correctness: " + str(bonus_correctness) +
                        " bonus from time: " + str(bonus_time))
        total_bonus = round(bonus_correctness + bonus_time, 2)

    total_pay = BASE_PAY + total_bonus

    resp = make_response(
        render_template(
            "results.html",
            AMAZON_HOST=AMAZON_HOST,
            percentage_correct=percentage_correct,
            num_correct=num_correct,
            num_questions=NUM_QUESTIONS,
            total_time=int(
                round(total_time/1000)),
            accept=accept,
            failure_reason=failure_reason,
            bonus_time=str(
                "{:.2f}".format(bonus_time)),
            bonus_correctness=str(
                "{:.2f}".format(bonus_correctness)),
            total_bonus=str(
                "{:.2f}".format(total_bonus)),
            total_pay=str(
                "{:.2f}".format(total_pay))
        ))
    resp.headers['x-frame-options'] = '*'
    return resp


if __name__ == "__main__":
    # app.debug = DEBUG
    app.init_db()
    app.run(threaded=True)

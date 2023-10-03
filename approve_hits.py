import sys
import boto3
import time
from datetime import datetime
import logging
import os
from models import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
import rd_study_server

# Heroku Database URL
DATABASE_URL = os.environ.get("REMOTE_DATABASE_URI").replace(
    "postgres://", "postgresql://", 1
)

appConfig = config.Config()


def get_connection():
    endpoint_url = ""
    if os.environ.get("AWS_SANDBOX") == "True":
        endpoint_url = "https://mturk-requester-sandbox.us-east-1.amazonaws.com"
    else:
        endpoint_url = "https://mturk-requester.us-east-1.amazonaws.com"

    return boto3.client(
        "mturk",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name="us-east-1",
        endpoint_url=endpoint_url,
    )


# Set up the MTurk connection
connection = get_connection()

# # The answers to the questions
# answers = json.loads(open("static/questions/answers.json").read())

# Database setup
engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
session = Session()

# Setup logging
log_filename = (
    "logs/approve_hits_" + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + ".log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m-%d-%y %H:%M:%S",
    filename=log_filename,
    filemode="a",
)

# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter("%(message)s")
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger("").addHandler(console)

logging.info("Starting run of approve_hits.py...")


# Returns the list of assignments with certain status for a given HITId
def get_assignment_hits(connection, hit_id, status):
    return connection.list_assignments_for_hit(
        HITId=hit_id, MaxResults=100, AssignmentStatuses=[status]
    )


NUM_QUESTIONS = 32


def approve_hits(connection, assignment_id_list, worker_id_list, test_only):
    with rd_study_server.app.app_context():  # needed to write to the database
        logging.info("Using database " + str(db))
        for i in range(len(assignment_id_list)):
            time.sleep(2)  # why?

            assignment_id = assignment_id_list[i]
            worker_id = worker_id_list[i]

            logging.info(
                "\nWorker "
                + str(i + 1)
                + "/"
                + str(len(assignment_id_list))
                + " --------- Evaluating "
                + assignment_id
                + " of worker "
                + worker_id
                + " ---------"
            )

            user = session.query(User).filter_by(worker_id=worker_id).first()

            # copied from rd_study_server.py
            num_answered = 0

            for question_num in range(1, NUM_QUESTIONS + 1):
                q_col = "q" + str(question_num)

                user_choice = getattr(user, q_col)

                # Our questions start at 1, our index starts at 0
                pattern_num = user.pattern_order[question_num - 1]

                if user_choice != None and user_choice != "":
                    num_answered = num_answered + 1
            # end copy

            if num_answered < NUM_QUESTIONS:
                raise Exception(
                    "Worker "
                    + worker_id
                    + " only answered "
                    + str(num_answered)
                    + "/"
                    + str(NUM_QUESTIONS)
                    + " questions! How did they get the assignment submitted!?"
                )

            if user.accept == None or user.accept == "":
                raise Exception(
                    "Null or blank value for the `accept` column in the database for worker "
                    + worker_id
                    + "! All submitted assignments should have `accept` set."
                )
            if not user.accept:
                if user.failure_reason == None:
                    raise Exception(
                        "`accept` is False but `failure_reason` is null in the database for worker "
                        + worker_id
                        + "! All rejected assignments should have `failure_reason` set."
                    )
                if user.failure_reason == "":
                    raise Exception(
                        "`accept` is False but `failure_reason` is the empty string in the database for worker "
                        + worker_id
                        + "! All rejected assignments should have `failure_reason` set."
                    )

            results_message = (
                " You answered "
                + str(user.number_correct)
                + "/"
                + str(NUM_QUESTIONS)
                + " correct and your time on questions and answers was "
                + "{:.2f}".format(
                    round(user.total_time_on_questions_and_answers / 60, 2)
                )
                + " min."
            )

            if not user.accept:
                reject_message = (
                    "We are sorry to inform you that your HIT has been rejected because "
                    + str(user.failure_reason)
                    + results_message
                    + ' Please recall the HIT description which reads "'
                    + "Workers should be familiar with SQL at the level of an advanced undergraduate database class, in particular with nested SQL queries."
                    + '" and "'
                    + "To successfully complete the HIT, you need to answer at least 16 questions correctly within 40 minutes."
                    + '" Recall also the consent form you agreed to at the beginning, which reads "'
                    + "Qualifications: We are asking you to participate in this study because you are experienced with using SQL"
                    + '" and "'
                    + "HIT acceptance criteria: You must answer 16 of the 32 questions correctly."
                    + '" You were also made aware that your HIT would be rejected on the final page before you submitted the HIT. Please write to us at nudatavisstudies@gmail.com if you believe we have made any errors and include your Mturk ID.'
                )

            logging.info(
                ("✅ ACCEPT" if user.accept else "❌ REJECT")
                + " worker "
                + worker_id
                + " assignment "
                + assignment_id
                + ". They had "
                + str(user.number_correct)
                + "/"
                + str(NUM_QUESTIONS)
                + " ("
                + str(round(user.percentage_correct * 100, 0))
                + "%)"
                + " correct. Time on Q&A was "
                + "{:.2f}".format(
                    round(user.total_time_on_questions_and_answers / 60, 2)
                )
                + " min. Pay: $"
                + "{:.2f}".format(round(user.total_pay_cents / 100, 2))
                + " (correctness +$"
                + "{:.2f}".format(round(user.bonus_correctness_cents / 100, 2))
                + ", time +$"
                + "{:.2f}".format(round(user.bonus_time_cents / 100, 2))
                + ")"
                + (
                    ""
                    if user.accept
                    else ' Rejection reason given: \n"' + reject_message + '"'
                )
            )

            if test_only:
                logging.info("Test only: Didn't accept/reject on MTurk.")
            else:
                logging.info("Actually accept/reject on MTurk.")

                # Approve or reject assignment accordingly
                if user.accept:
                    logging.info("Assignment " + assignment_id + " approved on MTurk")
                    approve_specific_assignment(assignment_id)
                else:
                    logging.info("Assignment " + assignment_id + " rejected on MTurk")
                    connection.reject_assignment(
                        AssignmentId=assignment_id,
                        RequesterFeedback=reject_message,
                    )

            if test_only:
                logging.info("Test only: Didn't update DB")
            else:
                logging.info("Actually updating that a payment was made in DB")
                user.accept_reject_sent = datetime.utcnow().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                db.session.commit()

            # # Send appropriate bonus if the assignment is accepted
            time.sleep(2)  # Why?
            if user.accept:
                logging.info("Calculating bonus for WorkerId: " + worker_id)
                send_bonus(worker_id, user, assignment_id, test_only)


def send_bonus(worker_id, user, assignment_id, test_only):
    bonus_correctness_dollars = round(user.bonus_correctness_cents / 100, 2)
    bonus_time_dollars = round(user.bonus_time_cents / 100, 2)
    total_bonus_dollars = round(user.total_bonus_cents / 100, 2)
    total_pay_dollars = round(user.total_pay_cents / 100, 2)

    if total_bonus_dollars > 0:
        reason_str = (
            "You received a total bonus of $"
            + "{:.2f}".format(total_bonus_dollars)
            + "—$"
            + "{:.2f}".format(bonus_correctness_dollars)
            + " due to your correctness and $"
            + "{:.2f}".format(bonus_time_dollars)
            + " due to your completion time, bringing your total pay to $"
            + "{:.2f}".format(total_pay_dollars)
            + ". Thank you again for participating in our study!"
        )

        logging.info(
            "Bonus message to Worker ID " + worker_id + ':\n"' + reason_str + '"'
        )
        if test_only:
            logging.info("Test only: Didn't bonus on MTurk.")
        else:
            logging.info("Actually bonusing on MTurk.")
            response = connection.send_bonus(
                WorkerId=worker_id,
                BonusAmount=str(total_bonus_dollars),
                AssignmentId=assignment_id,
                Reason=reason_str,
            )
            logging.info("Actually updating that a bonus was sent in DB.")
            user.bonus_sent = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            db.session.commit()
    else:
        logging.info("Worker ID: " + worker_id + " did not receive any bonus.")


def send_manual_bonus(worker_id, assignment_id):
    logging.info(
        "Sending manual bonus to worker "
        + worker_id
        + " for assignment "
        + assignment_id
    )
    with rd_study_server.app.app_context():  # needed to write to the database
        logging.info("Using database " + str(db))
        user = session.query(User).filter_by(worker_id=worker_id).first()
        send_bonus(worker_id, user, assignment_id, False)


# def send_bonus_error(worker_id, assignment_id):
#     total_bonus = "4.5"
#     reason_str = "Due to our issues with your HIT submission you have been compensated with the base pay. Your HIT is neither accepted nor rejected."
#     connection.send_bonus(
#         WorkerId=worker_id,
#         BonusAmount=str(total_bonus),
#         AssignmentId=assignment_id,
#         Reason=reason_str,
#     )
#     logging.info(
#         "Worker ID: "
#         + worker_id
#         + " with Assignment ID: "
#         + assignment_id
#         + " is payed as bonus the base pay due to issues with their HIT submission."
#     )


# # Evaluate the workers that failed the HIT initially and accept their hit if they had at least 1 right answer
# def re_evaluate_workers(connection, filename):
#     data = pd.read_csv(filename)
#     worker_id_list = data["worker_id"].values
#     assignment_id_list = data["assignment_id"].values

#     current_date = datetime.now().date()

#     min_allowed_correct = 1

#     for i in range(len(assignment_id_list)):
#         accept = True

#         assignment_id = assignment_id_list[i]
#         worker_id = worker_id_list[i]

#         # Check if the assignment was submitted less than a month ago
#         submit_date = connection.get_assignment(AssignmentId=assignment_id)[
#             "Assignment"
#         ]["SubmitTime"].date()
#         days_diff = (current_date - submit_date).days
#         print("Days Difference:", days_diff)

#         if days_diff < 30:
#             time.sleep(2)
#             logging.info(
#                 "--------------------- Evaluating "
#                 + assignment_id
#                 + " of worker "
#                 + worker_id
#                 + " ---------------------"
#             )
#             num_correct, total_time = get_score_and_time(assignment_id)
#             logging.info(
#                 "Assignment "
#                 + assignment_id
#                 + " had "
#                 + str(num_correct)
#                 + " correct and was completed in "
#                 + str(total_time / 1000)
#                 + " seconds"
#             )

#             # Check if the user answered 0 questions correctly
#             if num_correct < min_allowed_correct:
#                 accept = False
#                 logging.info("worker's " + worker_id + "HIT is REJECTED")
#             else:
#                 accept = True

#             # Approve or reject assignment accordingly
#             if accept:
#                 connection.approve_assignment(
#                     AssignmentId=assignment_id,
#                     RequesterFeedback="Congratulations! We have decided to accept your HIT after re-evaluating our acceptance criteria for the HIT. Thank you for your time! :)",
#                     OverrideRejection=True,
#                 )
#                 logging.info("worker's " + worker_id + "HIT is ACCEPTED")


def approve_specific_assignment(assignment_id):
    connection.approve_assignment(
        AssignmentId=assignment_id,
        RequesterFeedback="Congratulations! Your HIT has been approved. Thank you for your help with our study! :-) If you have any further feedback on our study, please write to us at nudatavisstudies@gmail.com and include your Mturk ID.",
        OverrideRejection=True,
    )


def reject_specific_assignment(assignment_id, feedback):
    connection.approve_assignment(
        AssignmentId=assignment_id,
        RequesterFeedback=feedback,
    )


def grade_specific_assignment(assignment_id, worker_id):
    approve_hits(connection, [assignment_id], [worker_id])


def batch_grade(hit_id, test_only=True):
    logging.info("batch grading HIT. Testing: " + str(test_only))
    assignments = get_assignment_hits(connection, hit_id, "Submitted")["Assignments"]
    assignment_id_list = []
    worker_id_list = []
    for i in assignments:
        assignment_id_list.append(i["AssignmentId"])
        worker_id_list.append(i["WorkerId"])

    for i in range(len(assignment_id_list)):
        logging.info(
            "worker_id: "
            + worker_id_list[i]
            + " with assignment: "
            + assignment_id_list[i]
        )
    logging.info(
        "There are "
        + str(len(assignment_id_list))
        + " assignments submitted waiting approval"
    )

    approve_hits(connection, assignment_id_list, worker_id_list, test_only)


if __name__ == "__main__":
    arg_arr = sys.argv[1:]
    arg0 = arg_arr[0]

    if arg0 == "batch_grade":
        hit_id = arg_arr[1]
        batch_grade(hit_id, False)
    elif arg0 == "batch_grade_test":
        hit_id = arg_arr[1]
        batch_grade(hit_id, True)
    elif arg0 == "send_manual_bonus":
        worker_id = arg_arr[1]
        assignment_id = arg_arr[2]
        send_manual_bonus(worker_id, assignment_id)
    elif arg0 == "reject":
        assignment_id = arg_arr[1]
        feedback = arg_arr[2]
        reject_specific_assignment(assignment_id, feedback)
    elif arg0 == "approve":
        assignment_id = arg_arr[1]
        approve_specific_assignment(assignment_id)
    elif arg0 == "grade":
        assignment_id = arg_arr[1]
        worker_id = arg_arr[2]
        grade_specific_assignment(assignment_id, worker_id)
    else:
        logging.error("Unknown argument: " + arg0)

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


# Set up the AMT connection
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


def approve_hits(connection, assignment_id_list, worker_id_list):
    with rd_study_server.app.app_context():
        for i in range(len(assignment_id_list)):
            time.sleep(2)

            assignment_id = assignment_id_list[i]
            worker_id = worker_id_list[i]

            logging.info("Worker " + str(i + 1) + "/" + str(len(assignment_id_list)))
            logging.info(
                "--------------------- Evaluating "
                + assignment_id
                + " of worker "
                + worker_id
                + " ---------------------"
            )

            user = session.query(User).filter_by(worker_id=worker_id).first()

            logging.info(
                "Assignment "
                + assignment_id
                + " by worker "
                + worker_id
                + " had "
                + str(user.number_correct)
                + " ("
                + str(round(user.percentage_correct, 2))
                + "%)"
                + " correct. Time on questions and answers was "
                + "{:.2f}".format(
                    round(user.total_time_on_questions_and_answers / 60, 2)
                )
                + " minutes."
                + (
                    "Accept"
                    if user.accept
                    else "Fail, reason given: " + user.failure_reason
                )
                + ". Total pay: $"
                + "{:.2f}".format(round(user.total_pay_cents / 100, 2))
                + " (bonuses for time: $"
                + "{:.2f}".format(round(user.bonus_time_cents / 100, 2))
                + ", correctness: $"
                + "{:.2f}".format(round(user.bonus_correctness_cents / 100, 2))
                + ")"
            )

            # Approve or reject assignment accordingly
            if user.accept:
                logging.info("Assignment " + assignment_id + " approved")
                approve_specific_assignment(assignment_id)
            else:
                logging.info("Assignment " + assignment_id + " rejected")
                connection.reject_assignment(
                    AssignmentId=assignment_id,
                    RequesterFeedback="We are sorry to inform you that your HIT has been rejected due to "
                    + user.failure_reason,
                )

            # Send appropriate bonus if the assignment is accepted
            time.sleep(2)
            if user.accept:
                logging.info("Calculating bonus for WorkerId: " + worker_id)
                send_bonus(user, assignment_id)
            user.accept_reject_sent = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            db.session.commit()


def send_bonus(user, assignment_id):
    bonus_correctness_dollars = round(user.bonus_correctness_cents / 100, 2)
    bonus_time_dollars = round(user.bonus_time_dollars / 100, 2)
    total_bonus_dollars = round(user.total_bonus_cents / 100, 2)
    total_pay_dollars = round(user.total_pay_cents / 100, 2)

    if total_bonus_dollars > 0:
        reason_str = (
            "You received a total bonus of $"
            + str(total_bonus_dollars)
            + ". $"
            + str(bonus_correctness_dollars)
            + " due to your correctness and $"
            + str(bonus_time_dollars)
            + " due to your completion time, bringing your total pay to "
            + str(total_pay_dollars)
            + "."
        )
        worker_id = (
            session.query(User).filter_by(assignment_id=assignment_id).first().worker_id
        )
        logging.info("Sending to Worker ID " + worker_id + ": " + reason_str)
        response = connection.send_bonus(
            WorkerId=worker_id,
            BonusAmount=str(total_bonus_dollars),
            AssignmentId=assignment_id,
            Reason=reason_str,
        )
    else:
        worker_id = (
            session.query(User).filter_by(assignment_id=assignment_id).first().worker_id
        )
        logging.info("Worker ID: " + worker_id + " did not receive any bonus.")
    user.bonus_sent = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.session.commit()


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
        RequesterFeedback="Congratulations! Your HIT has been approved. Thank you for your help with our study! :-)",
        OverrideRejection=True,
    )


def reject_specific_assignment(assignment_id, feedback):
    connection.approve_assignment(
        AssignmentId=assignment_id,
        RequesterFeedback=feedback,
    )


def grade_specific_assignment(assignment_id, worker_id):
    approve_hits(connection, [assignment_id], [worker_id])


def batch_grade(hit_id):
    logging.info("batch grading HIT")
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

    approve_hits(connection, assignment_id_list, worker_id_list)


if __name__ == "__main__":
    arg_arr = sys.argv[1:]
    arg0 = arg_arr[0]

    if arg0 == "batch_grade":
        hit_id = arg_arr[1]
        batch_grade(hit_id)
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

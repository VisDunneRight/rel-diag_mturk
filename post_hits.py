import sys
import os
import boto3
import config
import json
from datetime import date, datetime


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


# Start Configuration Variables
appConfig = config.Config()

# End Configuration Variables

# This allows us to specify whether we are pushing to the sandbox or live site.
if os.environ.get("AWS_SANDBOX") == "True":
    AMAZON_HOST = "mechanicalturk.sandbox.amazonaws.com"
    qualification_id = None
    custom_qualification_id = None
    taken_test_qualification_id = "3VFIQRXYYM783TDKWYVL8LHMWTBZ2U"
else:
    AMAZON_HOST = "mechanicalturk.amazonaws.com"
    qualification_id = None
    custom_qualification_id = None
    taken_test_qualification_id = "3VFIQRXYYM783TDKWYVL8LHMWTBZ2U"

# HIT specific variables
base_pay = "6"
approval_percentage = 97
approved_hits = 500
minimum_qualification_score = 66  # This is equivalent to 4/6 correct for Amazon

title_str = "Visualizing Database Queries -- $6.00 to $12.88 with bonuses"

description_str = "You will receive $6.00-$12.88 (estimated time 21 minutes) for participating in this research. Workers should be familiar with SQL at the level of an advanced undergraduate database class, in particular with nested SQL queries. The HIT is composed of 32 multiple choices questions that ask the user to find the correct description of an SQL query based on a text or visual representation. To successfully complete the HIT, you need to answer at least 16 questions correctly within 40 minutes. You receive bonuses if you get more correct answers and/or finish in shorter time. For more details, click on Preview to view the full instructions of the HIT. Please contact us with any questions or issues, especially if you get a 'Your HIT submission was not successful' error message."

usa = [{"Country": "US"}]


def get_connection():
    endpoint_url = ""
    if os.environ.get("AWS_SANDBOX") == "True":
        endpoint_url = "https://mturk-requester-sandbox.us-east-1.amazonaws.com"
    else:
        endpoint_url = "https://mturk-requester.us-east-1.amazonaws.com"

    print("using endpoint", endpoint_url)

    return boto3.client(
        "mturk",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name="us-east-1",
        endpoint_url=endpoint_url,
    )


def post_hit_helper(
    approved_hits,
    approval_percentage,
    max_assignments,
    lifetime_in_seconds,
    assignment_duration_in_seconds,
    base_reward,
    title,
    description,
    locales,
    qual_id,
    min_qual_score,
    test_taken_qual_id,
    custom_qual_id,
):
    connection = get_connection()

    questionform = open("external_question.xml", "r").read()

    # Boto3 version. Described here:
    # https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
    qualification_requirements = [
        {
            "QualificationTypeId": "00000000000000000071",  # Worker_Locale. The location of the Worker, as specified in the Worker's mailing address.
            "Comparator": "EqualTo",
            "LocaleValues": locales,
        },
        {
            "QualificationTypeId": "00000000000000000040",  # Worker_​NumberHITsApproved. Specifies the total number of HITs submitted by a Worker that have been approved. The value is an integer greater than or equal to 0.
            "Comparator": "GreaterThanOrEqualTo",
            "IntegerValues": [approved_hits],
        },
        {
            "QualificationTypeId": "000000000000000000L0",  # PercentAssignmentsApproved. The percentage of assignments the Worker has submitted that were subsequently approved by the Requester, over all assignments the Worker has submitted. The value is an integer between 0 and 100.
            "Comparator": "GreaterThanOrEqualTo",
            "IntegerValues": [approval_percentage],
        },
    ]

    if test_taken_qual_id != None:
        qualification_requirements.append(
            {
                "QualificationTypeId": test_taken_qual_id,
                "Comparator": "DoesNotExist",
            },
        )

    if qual_id != None:
        qualification_requirements.append(
            {
                "QualificationTypeId": qual_id,
                "Comparator": "GreaterThanOrEqualTo",
                "IntegerValues": [min_qual_score],
            }
        )

    if custom_qual_id != None:
        qualification_requirements.append(
            {"QualificationTypeId": custom_qual_id, "Comparator": "Exists"}
        )

    create_hit_result = connection.create_hit(
        Question=questionform,
        MaxAssignments=max_assignments,
        LifetimeInSeconds=lifetime_in_seconds,
        AssignmentDurationInSeconds=assignment_duration_in_seconds,
        Reward=base_reward,
        Title=title,
        Description=description,
        QualificationRequirements=qualification_requirements,
    )

    print(json.dumps(create_hit_result, default=json_serial, sort_keys=True, indent=4))

    print("Created a new HIT with HITId: " + create_hit_result["HIT"]["HITId"])


def post_hit():
    print("Creating normal HIT")
    post_hit_helper(
        approved_hits=approved_hits,
        approval_percentage=approval_percentage,
        max_assignments=50,
        lifetime_in_seconds=60 * 60 * 24 * 20,  # 20 days
        assignment_duration_in_seconds=60 * 50,  # 50 minutes
        base_reward=base_pay,
        title=title_str,
        description=description_str,
        locales=usa,
        qual_id=qualification_id,
        min_qual_score=minimum_qualification_score,
        test_taken_qual_id=taken_test_qualification_id,
        custom_qual_id=None,
    )


def pilot_post_hit():
    print("Creating pilot HIT")
    post_hit_helper(
        approved_hits=approved_hits,
        approval_percentage=approval_percentage,
        max_assignments=12,
        lifetime_in_seconds=60 * 60 * 24 * 1,  # 1 day
        assignment_duration_in_seconds=60 * 50,  # 50 minutes
        base_reward=base_pay,
        title=title_str,
        description=description_str,
        locales=usa,
        qual_id=qualification_id,
        min_qual_score=minimum_qualification_score,
        test_taken_qual_id=taken_test_qualification_id,
        custom_qual_id=None,
    )


def custom_post_hit(worker_id, custom_qual_id):
    print(
        "Creating custom HIT for worker "
        + worker_id
        + " with qualification "
        + custom_qual_id
    )
    post_hit_helper(
        approved_hits=approved_hits,
        approval_percentage=approval_percentage,
        max_assignments=1,
        lifetime_in_seconds=60 * 60 * 24 * 10,  # 10 days
        assignment_duration_in_seconds=60 * 50,  # 50 minutes
        base_reward=base_pay,
        title="CUSTOM HIT FOR WORKER " + worker_id + ", " + title_str,
        description=description_str,
        locales=usa,
        qual_id=qualification_id,
        min_qual_score=minimum_qualification_score,
        test_taken_qual_id=taken_test_qualification_id,
        custom_qual_id=custom_qual_id,
    )


if __name__ == "__main__":
    arg_arr = sys.argv[1:]
    arg0 = arg_arr[0]

    if arg0 not in ["full", "pilot", "custom", "test"]:
        print(
            "Invalid argument! Argument must be one of 'full', 'pilot', 'custom' or 'test'"
        )
        sys.exit()

    yes = {"yes", "y", "ye", ""}
    no = {"no", "n"}

    setting = "on SANDBOX" if (os.environ.get("AWS_SANDBOX") == "True") else "LIVE"
    print("Are you sure you want to deploy a " + arg0 + " HIT " + setting + "? [Y/N]")
    choice = input().lower()
    if choice in yes:
        if arg0 == "full":
            post_hit()
        elif arg0 == "pilot":
            pilot_post_hit()
        elif arg0 == "custom":
            custom_post_hit(arg_arr[1], arg_arr[2])
    elif choice in no:
        print("Execution cancelled")
    else:
        sys.stdout.write("Please respond with 'y' (yes) or 'n' (no)\n")

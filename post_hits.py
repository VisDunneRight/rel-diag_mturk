import sys
import os
import boto3
import config

# Start Configuration Variables
appConfig = config.Config()

# End Configuration Variables

# This allows us to specify whether we are pushing to the sandbox or live site.
if os.environ.get('AWS_SANDBOX') == 'True':
    AMAZON_HOST = "mechanicalturk.sandbox.amazonaws.com"         # For Sandbox only
    qualification_id = "AA"                        # For Sandbox only
    custom_qualification_id = "custom_qualification_id"          # For Sandbox only
    taken_test_qualification_id = "taken_test_qualification_id"  # For Sandbox only
else:
    AMAZON_HOST = "mechanicalturk.amazonaws.com"                 # For Non-Sandbox
    qualification_id = "AA"                        # For Non-Sandbox
    custom_qualification_id = "custom_qualification_id"          # For Non-Sandbox
    taken_test_qualification_id = "taken_test_qualification_id"  # For Non-Sandbox

# HIT specific variables
base_pay = "5"
approval_percentage = 95
minimum_qualification_score = 66    # This is equivalent to 4/6 correct for Amazon

title_str = "Visualizing Database Queries -- $5.20 to $16.47 with bonuses"

description_str = "You will receive $5.20-$16.47 (estimated time 30 minutes) for participating in this research. \
Workers must be experienced with SQL as measured by the qualification test (included in the 30 minutes estimate). \
The HIT is composed of 12 multiple choices questions that ask the user to find the correct description \
of a SQL query based on a text and/or visual representation. To successfully complete the HIT you need \
to answer at least 5 questions correctly within 50 minutes. You receive bonuses for more correct answers \
and in a shorter time. For more details click on Preview to view the full instructions of the HIT. \
Please contact us with any questions or issues, especially if you get a 'Your HIT submission \
was not successful' error message."

usa = [{'Country': "US"}]


def get_connection():
    endpoint_url = ''
    if os.environ.get('AWS_SANDBOX') == 'True':
        endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    else:
        endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'

    return boto3.client(
        'mturk',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get(
            'AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-1',
        endpoint_url=endpoint_url
    )


def post_hit_helper(approval_percentage, max_assignments, lifetime_in_seconds, assignment_duration_in_seconds, base_reward, title, description, locales, qual_id, min_qual_score, test_taken_qual_id, custom_qual_id):
    connection = get_connection()

    questionform = open("external_question.xml", 'r').read()

    # Boto3 version
    QualificationRequirements=[{'QualificationTypeId': qual_id,
                                'Comparator': 'GreaterThanOrEqualTo',
                                'IntegerValues': [min_qual_score],
                                },
                                {'QualificationTypeId': "00000000000000000071",# locale
                                'Comparator': 'EqualTo',
                                'LocaleValues': locales
                                },
                                {'QualificationTypeId': "000000000000000000L0",# The percentage of assignments the Worker has submitted that were subsequently approved by the Requester, over all assignments the Worker has submitted. The value is an integer between 0 and 100.
                                'Comparator': 'GreaterThanOrEqualTo',
                                'IntegerValues': [approval_percentage]
                                },
                                {'QualificationTypeId': test_taken_qual_id,
                                'Comparator': 'DoesNotExist',
                                }]
    if custom_qual_id != None:
        QualificationRequirements.append(
            {'QualificationTypeId': custom_qual_id,
             'Comparator': 'Exists'}
        )

    create_hit_result = connection.create_hit(
        Question=questionform,
        MaxAssignments=max_assignments,
        LifetimeInSeconds=lifetime_in_seconds,
        AssignmentDurationInSeconds=assignment_duration_in_seconds,
        Reward=base_reward,
        Title=title,
        Description=description,
    )

    print("Created a new HIT with HITId: " + create_hit_result['HIT']['HITId'])


def post_hit():
    print('Creating normal HIT')
    post_hit_helper(
        approval_percentage=approval_percentage,
        max_assignments=120,
        lifetime_in_seconds= 60 * 60 * 24 * 40, # 40 days
        assignment_duration_in_seconds= 60 * 60 * 2, #2 hours
        base_reward=base_pay,
        title = title_str,
        description=description_str,
        locales=usa,
        qual_id=qualification_id,
        min_qual_score=minimum_qualification_score,
        test_taken_qual_id=taken_test_qualification_id
    )

def pilot_post_hit():
    print('Creating pilot HIT')
    post_hit_helper(
        approval_percentage=approval_percentage,
        max_assignments=12,
        lifetime_in_seconds= 60 * 60 * 24 * 1, # 1 day
        assignment_duration_in_seconds= 60 * 60 * 2, #2 hours
        base_reward=base_pay,
        title = title_str,
        description=description_str,
        locales=usa,
        qual_id=qualification_id,
        min_qual_score=minimum_qualification_score,
        test_taken_qual_id=taken_test_qualification_id
    )

def custom_post_hit(worker_id, custom_qual_id):
    print('Creating custom HIT for worker ' + worker_id + ' with qualification ' + custom_qual_id)
    post_hit_helper(
        approval_percentage=approval_percentage,
        max_assignments=1,
        lifetime_in_seconds= 60 * 60 * 24 * 10, # 10 days
        assignment_duration_in_seconds= 60 * 60 * 2, # 2 hours
        base_reward=base_pay,
        title = 'CUSTOM HIT FOR WORKER ' + worker_id + ', ' + title_str,
        description=description_str,
        locales=usa,
        qual_id=qualification_id,
        min_qual_score=minimum_qualification_score,
        test_taken_qual_id=taken_test_qualification_id,
        custom_qual_id=custom_qual_id
    )


def create_multiple_hits():
    for i in range(5):
        title = "SQL Query Visualization " + str(i)
        post_hit(title)


if __name__ == "__main__":
    arg_arr = sys.argv[1:]
    arg1 = arg_arr[0]

    if arg1 not in ['full', 'pilot', 'custom', 'test']:
        print(
            "Invalid argument! Argument must be one of 'full', 'pilot', 'custom' or 'test'")
        sys.exit()

    yes = {'yes', 'y', 'ye', ''}
    no = {'no', 'n'}

    setting = "on SANDBOX" if (os.environ.get(
        'AWS_SANDBOX') == 'True') else "LIVE"
    print("Are you sure you want to deploy a " +
          arg1 + " HIT " + setting + "? [Y/N]")
    choice = input().lower()
    if choice in yes:
        if arg1 == 'full':
            post_hit()
        elif arg1 == 'pilot':
            pilot_post_hit()
        elif arg1 == 'custom':
            custom_post_hit(arg_arr[1], arg_arr[2])
    elif choice in no:
        print("Execution cancelled")
    else:
        sys.stdout.write("Please respond with 'y' (yes) or 'n' (no)\n")

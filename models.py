import enum
from sqlalchemy import Enum
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Sections(enum.Enum):
    INSTRUCTIONS = 1
    TUTORIAL = 2
    QUESTIONS = 3
    SURVEY = 4
    RESULTS = 5


# Create our database model


class User(db.Model):
    __tablename__ = "users"
    # Amazon variables
    worker_id = db.Column(db.String(), primary_key=True)
    assignment_id = db.Column(db.String())
    hit_id = db.Column(db.String())
    qualification_score = db.Column(db.Integer)

    # Current section and page within that section
    current_section = db.Column(Enum(Sections))
    current_page = db.Column(db.Integer)

    # Starting mode
    sequence_num = db.Column(db.Integer)

    # Pattern order
    pattern_order = db.Column(db.JSON)

    # Starting datetime of the entry
    start_datetime = db.Column(db.DateTime())
    end_datetime = db.Column(db.DateTime())

    # Time spent on the tutorial
    tutorial_time = db.Column(db.Integer)

    total_time_on_questions_and_answers = db.Column(db.Integer)
    total_question_time = db.Column(db.Integer)
    number_correct = db.Column(db.Integer)
    percentage_correct = db.Column(db.Float)

    accept = db.Column(db.Boolean)
    failure_reason = db.Column(db.String)
    bonus_correctness = db.Column(db.Float)
    bonus_time = db.Column(db.Float)
    total_bonus = db.Column(db.Float)
    total_pay = db.Column(db.Float)

    # Main test # there is probably a way to set static variables programmatically...
    # This is gross.
    q1 = db.Column(db.Integer)
    q1_start = db.Column(db.DateTime())
    q1_end = db.Column(db.DateTime())
    q1_time = db.Column(db.Integer)
    q2 = db.Column(db.Integer)
    q2_start = db.Column(db.DateTime())
    q2_end = db.Column(db.DateTime())
    q2_time = db.Column(db.Integer)
    q3 = db.Column(db.Integer)
    q3_start = db.Column(db.DateTime())
    q3_end = db.Column(db.DateTime())
    q3_time = db.Column(db.Integer)
    q4 = db.Column(db.Integer)
    q4_start = db.Column(db.DateTime())
    q4_end = db.Column(db.DateTime())
    q4_time = db.Column(db.Integer)
    q5 = db.Column(db.Integer)
    q5_start = db.Column(db.DateTime())
    q5_end = db.Column(db.DateTime())
    q5_time = db.Column(db.Integer)
    q6 = db.Column(db.Integer)
    q6_start = db.Column(db.DateTime())
    q6_end = db.Column(db.DateTime())
    q6_time = db.Column(db.Integer)
    q7 = db.Column(db.Integer)
    q7_start = db.Column(db.DateTime())
    q7_end = db.Column(db.DateTime())
    q7_time = db.Column(db.Integer)
    q8 = db.Column(db.Integer)
    q8_start = db.Column(db.DateTime())
    q8_end = db.Column(db.DateTime())
    q8_time = db.Column(db.Integer)
    q9 = db.Column(db.Integer)
    q9_start = db.Column(db.DateTime())
    q9_end = db.Column(db.DateTime())
    q9_time = db.Column(db.Integer)
    q10 = db.Column(db.Integer)
    q10_start = db.Column(db.DateTime())
    q10_end = db.Column(db.DateTime())
    q10_time = db.Column(db.Integer)
    q11 = db.Column(db.Integer)
    q11_start = db.Column(db.DateTime())
    q11_end = db.Column(db.DateTime())
    q11_time = db.Column(db.Integer)
    q12 = db.Column(db.Integer)
    q12_start = db.Column(db.DateTime())
    q12_end = db.Column(db.DateTime())
    q12_time = db.Column(db.Integer)
    q13 = db.Column(db.Integer)
    q13_start = db.Column(db.DateTime())
    q13_end = db.Column(db.DateTime())
    q13_time = db.Column(db.Integer)
    q14 = db.Column(db.Integer)
    q14_start = db.Column(db.DateTime())
    q14_end = db.Column(db.DateTime())
    q14_time = db.Column(db.Integer)
    q15 = db.Column(db.Integer)
    q15_start = db.Column(db.DateTime())
    q15_end = db.Column(db.DateTime())
    q15_time = db.Column(db.Integer)
    q16 = db.Column(db.Integer)
    q16_start = db.Column(db.DateTime())
    q16_end = db.Column(db.DateTime())
    q16_time = db.Column(db.Integer)
    q17 = db.Column(db.Integer)
    q17_start = db.Column(db.DateTime())
    q17_end = db.Column(db.DateTime())
    q17_time = db.Column(db.Integer)
    q18 = db.Column(db.Integer)
    q18_start = db.Column(db.DateTime())
    q18_end = db.Column(db.DateTime())
    q18_time = db.Column(db.Integer)
    q19 = db.Column(db.Integer)
    q19_start = db.Column(db.DateTime())
    q19_end = db.Column(db.DateTime())
    q19_time = db.Column(db.Integer)
    q20 = db.Column(db.Integer)
    q20_start = db.Column(db.DateTime())
    q20_end = db.Column(db.DateTime())
    q20_time = db.Column(db.Integer)
    q21 = db.Column(db.Integer)
    q21_start = db.Column(db.DateTime())
    q21_end = db.Column(db.DateTime())
    q21_time = db.Column(db.Integer)
    q22 = db.Column(db.Integer)
    q22_start = db.Column(db.DateTime())
    q22_end = db.Column(db.DateTime())
    q22_time = db.Column(db.Integer)
    q23 = db.Column(db.Integer)
    q23_start = db.Column(db.DateTime())
    q23_end = db.Column(db.DateTime())
    q23_time = db.Column(db.Integer)
    q24 = db.Column(db.Integer)
    q24_start = db.Column(db.DateTime())
    q24_end = db.Column(db.DateTime())
    q24_time = db.Column(db.Integer)
    q25 = db.Column(db.Integer)
    q25_start = db.Column(db.DateTime())
    q25_end = db.Column(db.DateTime())
    q25_time = db.Column(db.Integer)
    q26 = db.Column(db.Integer)
    q26_start = db.Column(db.DateTime())
    q26_end = db.Column(db.DateTime())
    q26_time = db.Column(db.Integer)
    q27 = db.Column(db.Integer)
    q27_start = db.Column(db.DateTime())
    q27_end = db.Column(db.DateTime())
    q27_time = db.Column(db.Integer)
    q28 = db.Column(db.Integer)
    q28_start = db.Column(db.DateTime())
    q28_end = db.Column(db.DateTime())
    q28_time = db.Column(db.Integer)
    q29 = db.Column(db.Integer)
    q29_start = db.Column(db.DateTime())
    q29_end = db.Column(db.DateTime())
    q29_time = db.Column(db.Integer)
    q30 = db.Column(db.Integer)
    q30_start = db.Column(db.DateTime())
    q30_end = db.Column(db.DateTime())
    q30_time = db.Column(db.Integer)
    q31 = db.Column(db.Integer)
    q31_start = db.Column(db.DateTime())
    q31_end = db.Column(db.DateTime())
    q31_time = db.Column(db.Integer)
    q32 = db.Column(db.Integer)
    q32_start = db.Column(db.DateTime())
    q32_end = db.Column(db.DateTime())
    q32_time = db.Column(db.Integer)

    # Survey
    feedback = db.Column(db.String())

    def __init__(self, worker_id=None, assignment_id=None, hit_id=None):
        self.worker_id = worker_id
        self.assignment_id = assignment_id
        self.hit_id = hit_id

    def __getitem__(self, field):
        return self.__dict__[field]

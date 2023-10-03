import dx_study_server
from dx_study_server import db
from models import User
import os

# create the database and the db table
with dx_study_server.app.app_context():
    db.create_all()

print("database table created!")

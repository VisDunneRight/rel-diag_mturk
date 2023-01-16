import rd_study_server 
from rd_study_server import db
from models import User
import os

# create the database and the db table
with rd_study_server.app.app_context():
    db.create_all()

print('database table created!')
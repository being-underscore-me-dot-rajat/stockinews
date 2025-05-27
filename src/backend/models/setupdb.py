import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import models  

with app.app_context():
    db.create_all()
    print("✅ SQLite DB and tables created")

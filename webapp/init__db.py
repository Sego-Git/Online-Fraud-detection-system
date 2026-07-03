from app import app
from extensions import db
import db_model

with app.app_context():
    db.create_all()
    print("✅ Database fraud.db created successfully")

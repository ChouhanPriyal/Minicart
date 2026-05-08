from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default="user")  

    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))

    address1 = db.Column(db.String(255))
    address2 = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id            = db.Column(db.Integer,   primary_key=True)
    full_name     = db.Column(db.String(150), nullable=False)
    username      = db.Column(db.String(100), unique=True, nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    role          = db.Column(db.String(50),  nullable=False, default='volunteer')
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)
    
    def get_reset_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset-salt', max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

class VolunteerEntry(db.Model):
    __tablename__ = 'volunteer_entry'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user        = db.relationship('User', backref=db.backref('entries', lazy=True))
    date        = db.Column(db.String(10))
    name        = db.Column(db.String(100))
    event       = db.Column(db.String(200))
    start_time  = db.Column(db.String(5))
    end_time    = db.Column(db.String(5))
    total_hours = db.Column(db.Float)
    notes       = db.Column(db.String(300))

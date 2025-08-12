from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from sqlalchemy.orm import validates

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    role = db.Column(db.String(20))  # 'admin' or 'participant'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submissions = db.relationship('Submission', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_random_password(length=12):
        import random
        import string
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))

    def update_password(self, new_password):
        self.set_password(new_password)
        db.session.commit()
    
    @property
    def contests(self):
        """Get all contests this user participates in"""
        from sqlalchemy import select
        from sqlalchemy.orm import aliased
        
        # Use a subquery to get contest IDs from the association table
        contest_ids = db.session.execute(
            select(contest_participants.c.contest_id)
            .where(contest_participants.c.user_id == self.id)
        ).scalars().all()
        
        # Return Contest objects
        return Contest.query.filter(Contest.id.in_(contest_ids)).all()

class Contest(db.Model):
    __tablename__ = 'contests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_public = db.Column(db.Boolean, default=False)
    problems = db.relationship('Problem', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    participants = db.relationship('User', secondary='contest_participants', lazy='dynamic')
    participants_folder = db.Column(db.String(256), nullable=True)  # Path to the folder containing participant files
    
    def is_active(self):
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time

class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id', ondelete='CASCADE'))
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    time_limit = db.Column(db.Integer)
    expected_input = db.Column(db.Text)
    expected_output = db.Column(db.Text)
    submissions = db.relationship('Submission', backref='problem', lazy='dynamic', cascade='all, delete-orphan')
    test_cases = db.relationship('TestCase', backref='problem', lazy='dynamic', cascade='all, delete-orphan')


class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id', ondelete='CASCADE'))
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id', ondelete='CASCADE'))
    code = db.Column(db.Text)
    language = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(50))  # 'Pending', 'Accepted', etc.
    execution_time = db.Column(db.Float)  # in seconds
    
    @validates('execution_time')
    def validate_execution_time(self, key, value):
        if value is not None and value < 0:
            raise ValueError('Execution time cannot be negative')
        return value
    error_message = db.Column(db.Text)  # Store error messages from judge

contest_participants = db.Table('contest_participants',
    db.Column('contest_id', db.Integer, db.ForeignKey('contests.id', ondelete='CASCADE')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
)

class TestCase(db.Model):
    __tablename__ = 'test_cases'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False)
    expected_input = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_sample = db.Column(db.Boolean, default=False)

class ParticipantsHistory(db.Model):
    __tablename__ = 'participants_history'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    email = db.Column(db.String(120))
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id', ondelete='CASCADE'))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
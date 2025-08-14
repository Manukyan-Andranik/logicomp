from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from sqlalchemy.orm import validates
from sqlalchemy import Index

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    role = db.Column(db.String(20))  # 'admin' or 'participant'
    created_at = db.Column(db.DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))  # Fixed: UTC by default
    submissions = db.relationship('Submission', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
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
        from sqlalchemy import select
        contest_ids = db.session.execute(
            select(contest_participants.c.contest_id)
            .where(contest_participants.c.user_id == self.id)
        ).scalars().all()
        return Contest.query.filter(Contest.id.in_(contest_ids)).all()

class Contest(db.Model):
    __tablename__ = 'contests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime(timezone=True), index=True, nullable=False)  # Fixed: Non-nullable
    end_time = db.Column(db.DateTime(timezone=True), index=True, nullable=False)    # Fixed: Non-nullable
    is_public = db.Column(db.Boolean, default=False, index=True)
    problems = db.relationship('Problem', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    participants = db.relationship('User', secondary='contest_participants', lazy='dynamic')
    participants_folder = db.Column(db.String(256), nullable=True)
    
    __table_args__ = (
        Index('ix_contest_time_range', 'start_time', 'end_time'),
        Index('ix_contest_active_public', 'is_public', 'start_time', 'end_time'),
    )
    
    def is_active(self):
        now = datetime.now(timezone.utc)  # Fixed: Compare with UTC
        return self.start_time <= now <= self.end_time  # Now safe (both timezone-aware)

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
    timestamp = db.Column(db.DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))  # Fixed: UTC by default
    status = db.Column(db.String(50), index=True)
    execution_time = db.Column(db.Float)
    error_message = db.Column(db.Text)
    
    __table_args__ = (
        Index('ix_submission_user_contest', 'user_id', 'contest_id'),
        Index('ix_submission_problem_status', 'problem_id', 'status'),
        Index('ix_submission_contest_timestamp', 'contest_id', 'timestamp'),
        Index('ix_submission_user_timestamp', 'user_id', 'timestamp'),
    )
    
    @validates('execution_time')
    def validate_execution_time(self, key, value):
        if value is not None and value < 0:
            raise ValueError('Execution time cannot be negative')
        return value

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
    is_sample = db.Column(db.Boolean, default=False, index=True)

class ParticipantsHistory(db.Model):
    __tablename__ = 'participants_history'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    email = db.Column(db.String(120))
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))  # Fixed: UTC by default


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
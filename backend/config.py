import os
from dotenv import load_dotenv
from flask_mail import Message
from flask import current_app

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    template_folder='../frontend/templates'  
    static_folder='../frontend/static'       
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://olympiad:olympiad@localhost/olympiad'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMINS = ['admin@olympiad.example.com']
    SUBMISSIONS_PER_PAGE = 10
    CONTESTS_PER_PAGE = 10
    PROBLEMS_PER_PAGE = 10

    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') 
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
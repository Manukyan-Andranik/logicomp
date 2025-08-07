from flask import render_template, current_app
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_credentials_email(email, username, password, contest):
    send_email(
        f'Your credentials for {contest.title}',
        sender=current_app.config['ADMINS'][0],
        recipients=[email],
        text_body=render_template('email/credentials.txt',
                                username=username,
                                password=password,
                                contest=contest),
        html_body=render_template('email/credentials.html',
                                username=username,
                                password=password,
                                contest=contest)
    )
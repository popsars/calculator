# -*- coding: utf-8 -*-
import threading
from flask import render_template
from flask_mail import Message
from typing import List
from app import app, mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject: str, sender: str, recipients: List[str], text_body: str, html_body: str):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    threading.Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        '[Microblog] Reset Your Password',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body='',
        html_body=render_template('email/reset_password_mail.html', user=user, token=token)
    )

# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
# from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False

    SECRET_KEY = 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir}/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTS_PER_PAGE = 10

    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = '927872@qq.com'
    MAIL_PASSWORD = 'wmkytvztlmdjbhdg'
    ADMINS = ['927872@qq.com']


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
# migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
moment = Moment(app)

from app import models, errors
from app.main import routes

import logging
from logging.handlers import RotatingFileHandler, SMTPHandler


if not app.debug:
    # 通过电子邮件发送错误
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    # 记录日志到文件中
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog startup')

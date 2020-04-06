# -*- coding: utf-8 -*-
import logging
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_compress import Compress
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required, user_logged_in


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ybk'
login_manager = LoginManager()
login_manager.init_app(app)
compress = Compress()
compress.init_app(app)


class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    print('unauthorized...')
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(somewhere)


@app.route('/')
@login_required
def index():
    """ 首页
    管理员重定向到后台
    客户重定向到前台
    """
    print(f'current_user: {current_user}')
    return
    if current_user.is_admin:
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('front'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18181, threaded=True)

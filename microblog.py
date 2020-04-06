# -*- coding: utf-8 -*-
# pip install flask, flask-login, flask_migrate, flask-openid, flask-mail, flask-sqlalchemy, sqlalchemy-migrate, flask-whooshalchemy, flask-wtf, flask-babel, flup, pyjwt
# pip install bootstrap-flask
# https://getbootstrap.com/docs/4.4/getting-started/download/
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xi-facelift
# https://github.com/miguelgrinberg/microblog/
# https://blog.csdn.net/weixin_42126327/category_7941651.html

from flask import render_template
from flask_login import login_required
from app import app, db
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}


if __name__ == '__main__':
    db.create_all()
    print(User.query.all())
    print(Post.query.all())

    # # 添加用户
    # usernames = ['927872', '13816992232', 'test', 'temp', 'admin']
    # for username in usernames:
    #     user = User(username=username, email=f'{username}@qq.com')
    #     user.set_password('P@ssw0rd')
    #     db.session.add(user)
    # db.session.commit()
    #
    # # 添加评论
    # for i, username in enumerate(usernames):
    #     user = User.query.filter_by(username=username).first()
    #     for j in range(10 * (i + 1)):
    #         post = Post(body=f'这是我的第{j + 1}篇评论', author=user)
    #         db.session.add(post)
    # db.session.commit()

    app.run(host='0.0.0.0', port=80, threaded=True, debug=False)

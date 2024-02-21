from flask import Flask
from flask import render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.String, nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(12))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        posts = Post.query.all()
        return render_template('index.html', posts=posts)
    else:
        session.permanent = True
        search = request.form.get('search')
        sort = request.form.get('sort')

        if search is None or len(search) == 0:
            posts = Post.query.all()

            if sort == 'sort_new':
                posts = Post.query.order_by(Post.created_at.desc())

            elif sort == 'sort_old':
                posts = Post.query.order_by(Post.created_at)

            elif sort == 'sort_title':
                posts = Post.query.order_by(Post.title)
        else:
            posts = Post.query.filter(
                or_(Post.body.contains(search), Post.title.contains(search)))
            session['search'] = search
            search = session['search']

            if sort == 'sort_new':
                posts = Post.query.filter(or_(Post.body.contains(
                    search), Post.title.contains(search))).order_by(Post.created_at.desc())
            elif sort == 'sort_old':
                posts = Post.query.filter(or_(Post.body.contains(
                    search), Post.title.contains(search))).order_by(Post.created_at)

            elif sort == 'sort_title':
                posts = Post.query.filter(or_(Post.body.contains(
                    search), Post.title.contains(search))).order_by(Post.title)

        return render_template('index.html', posts=posts, search=search)


@app.route('/index/opt', methods=['GET', 'POST'])
def login_opt():
    if request.method == 'GET':
        posts_opt = Post.query.all()
        return render_template('index_opt.html', posts_opt=posts_opt)
    else:
        session.permanent = True
        search_opt = request.form.get('search_opt')
        sort_opt = request.form.get('sort_opt')

        if search_opt is None or len(search_opt) == 0:
            posts_opt = Post.query.all()

            if sort_opt == 'sort_new':
                posts_opt = Post.query.order_by(Post.created_at.desc())

            elif sort_opt == 'sort_old':
                posts_opt = Post.query.order_by(Post.created_at)

            elif sort_opt == 'sort_title':
                posts_opt = Post.query.order_by(Post.title)
        else:
            posts_opt = Post.query.filter(
                or_(Post.body.contains(search_opt), Post.title.contains(search_opt)))
            session['search_opt'] = search_opt
            search_opt = session['search_opt']

            if sort_opt == 'sort_new':
                posts_opt = Post.query.filter(or_(Post.body.contains(
                    search_opt), Post.title.contains(search_opt))).order_by(Post.created_at.desc())
            elif sort_opt == 'sort_old':
                posts_opt = Post.query.filter(or_(Post.body.contains(
                    search_opt), Post.title.contains(search_opt))).order_by(Post.created_at)

            elif sort_opt == 'sort_title':
                posts_opt = Post.query.filter(or_(Post.body.contains(
                    search_opt), Post.title.contains(search_opt))).order_by(Post.title)

        return render_template('index_opt.html', posts_opt=posts_opt, search_opt=search_opt)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username, password=generate_password_hash(
            password, method='sha256'))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user == None or '':
            flash('ユーザー名が正しくありません')
            return redirect('/login')
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/index/opt')
        else:
            flash('パスワードが正しくありません')
            return redirect('/login')
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        file = request.files.get('image')
        filename = file.filename
        create_at = datetime.now(pytz.timezone('Asia/Tokyo'))

        if title == '' or body == '' or filename == '':
            flash('記入漏れがあります')
            return redirect('/create')
        else:
            post = Post(title=title, body=body,
                        created_at=create_at, image=filename)
            file.save(os.path.join('./static/images', filename))
            db.session.add(post)
            db.session.commit()
            return redirect('/index/opt')
    else:
        return render_template('create.html')


@app.route('/<int:id>/update', methods=['GET', 'POST'])
def update(id):
    post = Post.query.get(id)
    if request.method == 'GET':
        return render_template('update.html', post=post)
    else:
        post.title = request.form.get('title')
        post.body = request.form.get('body')
        file = request.files.get('image')
        post.image = file.filename
        file.save(os.path.join('./static/images', post.image))

        db.session.commit()
        return redirect('/index/opt')


@app.route('/<int:id>/delete', methods=['GET'])
def delete(id):
    post = Post.query.get(id)

    db.session.delete(post)
    db.session.commit()
    return redirect('/index/opt')


@app.route('/<int:id>/article', methods=['GET'])
def article(id):
    post = Post.query.get(id)
    return render_template('article.html', post=post)


if __name__ == ('__main__'):
    app.run(debug=True)

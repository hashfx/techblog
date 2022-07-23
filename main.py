import math
import os
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
from datetime import datetime
import json

# read config.json
with open('config.json', 'r') as c:
    params = json.load(c)['params']

local_server = True  # if True, then run on local server; if False, then run on heroku
app = Flask(__name__)
app.secret_key = 'my-secret-key'  # flask secret key
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)

mail = Mail(app)

# mysql uniform resource identifier: 'databaseName://user:password@host:port/table/db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/techblog'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/techblog'

# if on local server
# if (local_server):
#     app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']  # set the local URI
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']  # set URI to Production Server
db = SQLAlchemy(app)  # initialise the database


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(25), nullable=True)
    email = db.Column(db.String(20), nullable=False)

    def __init__(self, sno, name, phone_num, msg, date, email):
        self.sno = sno
        self.name = name
        self.phone_num = phone_num
        self.msg = msg
        self.date = date
        self.email = email

    #
    def __repr__(self):
        return '<Contacts %r>' % self.name


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subtitle = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(25), nullable=True)
    img_file = db.Column(db.String(25), nullable=True)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # if user is already logged in
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)  # display dashboard without login prompt

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == params['admin_user'] and password == params['admin_password']:
            # set session variable
            session['user'] = username  # session variable: user :: value: username
            # fetch all posts from database to display on admin panel
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    else:
        return render_template('login.html', params=params)


@app.route("/")
def home():
    # fetch all posts from database to display on home page
    posts = Posts.query.filter_by().all()  # get the first {no_of_posts} posts
    last = math.ceil(len(posts) / int(params['no_of_posts']))  # greatest integer function
    """ pagination logic
    first page: prev url='/' next url='page+1'
    middle page: prev url='page-1' next url='page+1'
    last page: prev url='page-1' next url='#'
    """
    page = request.args.get('page')  # GET request for page
    if (not str(page).isnumeric()):  # if page is number
        page = 1  # initial page = 1
    page = int(page)  # convert page to integer
    # slicing posts to display only {no_of_posts} posts
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(params['no_of_posts'])]

    # first page
    if (page == 1):
        prev = '#'
        next = '/?page=' + str(page + 1)
    # last page
    elif (page == last):
        prev = '/?page=' + str(page - 1)
        next = '#'
    # middle page
    else:
        prev = '/?page=' + str(page - 1)
        next = '/?page=' + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)  # params from config.json


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/logout")
def logout():
    # kill session to logout user
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    # check if user is logged in
    if ('user' in session and session['user'] == params['admin_user']):
        # sno = request.form.get('sno')
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)  # delete from database
        db.session.commit()  # commit recent changes
    return redirect('/dashboard')


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    # check if user is logged in
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == "POST":
            f = request.files['file']  # fetch file from request
            # save file
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            # secure_filename: remove special characters from file name and prohibits file name with ../../ and more
            return "File Uploaded successfully"


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        # fetch entries from database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # add entries to database
        # entry = Contacts(name=name, phone_num=phone, msg=message, email=email)
        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)

        # transaction control language
        db.session.add(entry)
        db.session.commit()
        # message through Flask Mail
        mail.send_message(
            'New message from: ' + name,
            sender=email,
            recipients=[params['gmail-user']],
            body=message + "\n" + phone
        )

    return render_template('contact.html', params=params)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    # check if user is logged in
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            # sno won't be changed being it a Primary Key
            edit_title = request.form.get('title')
            edit_subtitle = request.form.get('subtitle')
            edit_slug = request.form.get('slug')
            edit_content = request.form.get('content')
            edit_img = request.form.get('img')
            edit_date = datetime.now()

            # if sno is 0, new post is written; else existing post is being edited
            if sno == 'new':
                post = Posts(title=edit_title, subtitle=edit_subtitle, slug=edit_slug, content=edit_content,
                             img_file=edit_img, date=edit_date)
                db.session.add(post)
                db.session.commit()
            # fetch existing post to edit
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = edit_title
                post.slug = edit_slug
                post.subtitle = edit_subtitle
                post.content = edit_content
                post.img_file = edit_img
                post.date = edit_date
                db.session.commit()
                return redirect('/edit/' + sno)  # redirect to

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)

    # else:
    #     return render_template('login.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    # fetch posts from database
    post = Posts.query.filter_by(slug=post_slug).first()  # fetch the first post with the slug

    return render_template('post.html', params=params, post=post)


app.run(debug=True)

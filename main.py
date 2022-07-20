from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_mail import Mail
from datetime import datetime
import json

# read config.json
with open('config.json', 'r') as c:
    params = json.load(c)['params']

local_server = True  # if True, then run on local server; if False, then run on heroku
app = Flask(__name__)
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
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(25), nullable=True)
    img_file = db.Column(db.String(25), nullable=True)


@app.route("/")
def home():
    return render_template('index.html', params=params)  # params from config.json


@app.route("/about")
def about():
    return render_template('about.html', params=params)


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
        mail.send_message(
            'New message from: ' + name,
            sender=email,
            recipients=[params['gmail-user']],
            body=message + "\n" + phone
        )

    return render_template('contact.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    # fetch posts from database
    post = Posts.query.filter_by(slug=post_slug).first()  # fetch the first post with the slug

    return render_template('post.html', params=params, post=post)


app.run(debug=True)

import os
from PIL import Image

import secrets
from flask import render_template, url_for, flash, redirect, request
from flask_login.utils import login_required, login_user, current_user, logout_user
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskblog.models import User, Post

posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!plz login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():  # forms ke validations check kr deta hai
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            # ternary condition
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    # to avoid collision of the images...we convert it into image name random hex value
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    # form_picture.filename--> xyz.jpg asel tr fname madhe xyz ani f_ext madhe jpg store hote
    picture_fn = random_hex+f_ext  # ata image ch nav randomvalue.jpg hooin
    picture_path = os.path.join(
        app.root_path, 'static/profile_pics', picture_fn)
    # app.route.path--> aplya app directory madhe cursor yete ,tyanntr static/profile_pics tyapudhe attach hote ani nntr picture_fn(apli profile pic ji apan update karat ahot ti) tyala attach hote
    output_size = (125, 125)  # image_resize size
    i = Image.open(form_picture) #from pillow package
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    accountform = UpdateAccountForm()
    if accountform.validate_on_submit():
        if accountform.picture.data:
            picture_file = save_picture(accountform.picture.data)
            current_user.image_file = picture_file
        current_user.username = accountform.username.data
        current_user.email = accountform.email.data
        db.session.commit()
        flash('your account has been updated successfully', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        accountform.username.data = current_user.username
        accountform.email.data = current_user.email

    image_file = url_for(
        'static', filename='profile_pics/'+current_user.image_file)
    return render_template('account.html', title='account', image_file=image_file, form=accountform)

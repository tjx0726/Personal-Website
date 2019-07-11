import os
from app import app, db
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, PostForm
# user db
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Mat, Post

per_page = 10


@app.route('/protected/files/mat/<filename>')
@login_required
def mat_files(filename):
    allowed = False
    for p in current_user.mats:
        if p.answer_path == '/files/mat/'+filename:
            allowed = True
    if 'websolutions' in filename and not allowed and not current_user.is_admin:
        flash("You don't have access to {}".format(filename))
        return redirect('mat')
    else:
        return send_from_directory(
            os.path.join(app.instance_path, 'protected/files/mat'),
            filename)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')

            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data,
                        firstname=form.firstname.data, lastname=form.lastname.data)
        new_user.set_password(form.password.data)
        specs = Mat.query.filter(Mat.name.contains('Spec')).all()
        for paper in specs:
            new_user.mats.append(paper)
        db.session.add(new_user)
        db.session.commit()
        new_user.post('Hi everyone, I have registered this account.')
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out.')
    return redirect(url_for('index'))


@app.route('/mat')
@login_required
def mat():
    mat_papers = Mat.query.order_by(Mat.name.desc()).all()
    return render_template('mat.html', title='MAT', papers=mat_papers)


@app.route('/user/<username>/<page>')
@login_required
def user(username, page):
    user = User.query.filter_by(username=username).first_or_404()
    num_posts = user.posts.count()
    total_page = (num_posts-1)/per_page + 1
    if num_posts == 0:
        return redirect(url_for('user_default', username=username))
    if not page.isdigit():
        return redirect(url_for('index'))
    elif 0 < int(page) <= total_page:
        all_posts = user.posts.order_by(Post.timestamp.desc()).all()
        page = int(page)
        return render_template('user.html', title=username, user=user,
                               posts=all_posts[per_page *
                                               (page-1):min(per_page*(page),
                                                            num_posts)],
                               page=page, total_page=total_page)
    elif page == '0':
        return redirect(url_for('user', username=username, page=1))
    else:
        return redirect(url_for('user', username=username, page=total_page))


@app.route('/user')
@login_required
def user_no():
    username = current_user.username
    return redirect(url_for('user_default', username=username))


@app.route('/user/<username>')
@login_required
def user_default(username):
    user = User.query.filter_by(username=username).first_or_404()
    num_posts = user.posts.count()
    if num_posts == 0:
        return render_template('user.html', title=username, user=user,
                               posts=[], page=0, total_page=0)
    else:
        return redirect(url_for('user', username=username, page=1))


@app.route('/discussion/<page>')
@login_required
def discussion(page):
    num_posts = Post.query.count()
    total_page = (num_posts-1)/per_page+1
    if num_posts == 0:
        return redirect(url_for('discussion_no_page'))
    if not page.isdigit():
        return redirect(url_for('index'))
    elif 0 < int(page) <= total_page:
        all_posts = Post.query.order_by(Post.timestamp.desc()).all()
        page = int(page)
        return render_template('discussion.html', title='Discussion Panel',
                               posts=all_posts[per_page *
                                               (page-1):min(per_page*(page), num_posts)],
                               page=page, total_page=total_page)
    elif page == '0':
        return redirect(url_for('discussion', page=1))
    else:
        return redirect(url_for('discussion', page=total_page))


@app.route('/discussion')
@login_required
def discussion_no_page():
    num_posts = Post.query.count()
    if num_posts == 0:
        return render_template('discussion.html', title='Discussion Panel', posts=[], page=0,
                               total_page=1)
    else:
        return redirect(url_for('discussion', page=1))


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    form = PostForm()
    if form.validate_on_submit():
        user = current_user
        user.post(form.post.data)
        flash('You have posted a new message')
        return redirect(url_for('discussion', page=1))
    return render_template('post.html', title='Post a Message', form=form)


def admin_requirement(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            if current_user.is_admin:
                return f(*args, **kwargs)
            else:
                flash('You have no access to admin contents.')
                return redirect(url_for('index'))
        except:
            flash('You have no access to admin contents.')
            return redirect(url_for('index'))
    return wrap


@app.route('/user_management', methods=['GET', 'POST'])
@login_required
@admin_requirement
def user_management():
    users = User.query.order_by(User.id).all()
    return render_template('user_management.html', title='User Management',
                           users=users)

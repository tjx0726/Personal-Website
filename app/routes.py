import os
from app import app, db
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app.forms import *
# user db
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Mat, Post, Mat_result, Ps_files

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


@app.route('/protected/files/ps/<username>/<filename>')
@login_required
def ps_files(username, filename):
    allowed = False
    if current_user.username == username:
        allowed = True
    for ps in current_user.ps_own:
        if ps.file_name == filename:
            allowed = True
    for ps in current_user.ps_by_me:
        if ps.file_name == filename:
            allowed = True
    print(allowed)

    if 'websolutions' in filename and not allowed and not current_user.is_admin:
        flash("You don't have access to {}".format(filename))
        return redirect('ps_management')
    else:
        return send_from_directory(
            os.path.join(app.instance_path,
                         'protected/files/ps/{}'.format(username)), filename)


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
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        new_user = User(username=username, email=form.email.data,
                        firstname=form.firstname.data, lastname=form.lastname.data)
        new_user.set_password(form.password.data)
        specs = Mat.query.filter(Mat.name.contains('Spec')).all()
        for paper in specs:
            new_user.mats.append(paper)
        # mkdir for this user
        os.mkdir(os.path.join(app.instance_path,
                              'protected/files/ps/{}'.format(username)))
        db.session.add(new_user)
        db.session.commit()
        if current_user.is_admin:
            new_user.post('Hi')
            flash('You have added a new user {}.'.format(new_user.username))
            return redirect(url_for('user_management'))
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


@app.route('/mat/my_result')
@login_required
def mat_my_results():
    user = current_user
    data = []
    mats = Mat.query.order_by(Mat.name.desc()).all()
    for mat in mats:
        m = {}
        data.append(m)
        m['name'] = mat.name
        m['results'] = []
        for result in mat.results.order_by(Mat_result.user_id).all():
            if result.student == user:
                r = {}
                r['id'] = result.student.id
                r['result_id'] = result.id
                r['timestamp'] = result.timestamp
                r['1'] = result.q1_score
                r['2'] = result.q2_score
                r['3'] = result.q3_score
                r['4'] = result.q1_score
                r['5'] = result.q1_score
                r['6'] = result.q1_score
                r['7'] = result.q7_score
                r['total'] = result.total_score
                m['results'].append(r)

    return render_template('mat_management_user.html', title='My MAT Results', mats=data, user=user)


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
        '''
        try:
            if current_user.is_admin:
                return f(*args, **kwargs)
            else:
                flash('You have no access to admin contents.')
                return redirect(url_for('index'))
        except Exception as e:
            raise e
            #print(e)
            #flash(e.args)
            return redirect(url_for('index'))
        '''
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            flash('You have no access to admin contents.')
            return redirect(url_for('index'))
    return wrap


@app.route('/management/user_management')
@login_required
@admin_requirement
def user_management():
    users = User.query.order_by(User.id).all()
    return render_template('user_management.html', title='User Management',
                           users=users)


@app.route('/management/user_management/delete/<username>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def delete_user_confirm(username):
    form = DeleteSub()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        user.delete()
        flash('User {} has been deleted.'.format(username))
        return redirect(url_for('user_management'))
    return render_template('delete_confirm.html',
                           title='Delete User {}'.format(username),
                           form=form,
                           message="Deleting a user is not recoverable.",
                           back="User Management",
                           back_url=url_for('user_management')
                           )


@app.route('/management/user_management/delete_user_post/<username>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def delete_user_post_confirm(username):
    form = DeleteSub()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        user.delete_posts()
        flash('Messages posted by user {} has been deleted.'.format(username))
        return redirect(url_for('user_management'))
    return render_template('delete_confirm.html',
                           title='Delete Posts by {}'.format(username),
                           form=form,
                           message="Deleting posts is not recoverable.",
                           back="User Management",
                           back_url=url_for('user_management')
                           )


@app.route('/management/user_management/change_admin/<username>')
@login_required
@admin_requirement
def change_admin(username):
    user = User.query.filter_by(username=username).first_or_404()
    user.change_admin()
    return redirect(url_for('user_management'))


@app.route('/management/student_management', methods=['GET', 'POST'])
@login_required
@admin_requirement
def student_management():
    students = User.query.filter_by(is_admin=False).order_by(User.id).all()
    return render_template('student_management.html', title='Student Management',
                           students=students)


@app.route('/management/mat_management')
@login_required
@admin_requirement
def mat_management():
    data = []
    mats = Mat.query.order_by(Mat.name.desc()).all()
    for mat in mats:
        m = {}
        data.append(m)
        m['name'] = mat.name
        m['results'] = []
        prev_id = 0
        prev_timestamp = 0
        for result in mat.results.order_by(Mat_result.user_id).all():
            r = {}
            r['user'] = result.student
            r['id'] = result.student.id
            r['result_id'] = result.id
            r['timestamp'] = result.timestamp
            r['1'] = result.q1_score
            r['2'] = result.q2_score
            r['3'] = result.q3_score
            r['4'] = result.q1_score
            r['5'] = result.q1_score
            r['6'] = result.q1_score
            r['7'] = result.q7_score
            r['total'] = result.total_score

            if prev_id == r['id']:
                if result.timestamp > prev_timestamp:
                    m['results'][-1] = r
            else:
                m['results'].append(r)
            prev_id = r['id']
            prev_timestamp = result.timestamp
    return render_template('mat_management.html', title='Mat Management',
                           mats=data)


@app.route('/mat_management/user/<username>')
@login_required
@admin_requirement
def mat_management_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    data = []
    mats = Mat.query.order_by(Mat.name.desc()).all()
    for mat in mats:
        m = {}
        data.append(m)
        m['name'] = mat.name
        m['results'] = []
        for result in mat.results.order_by(Mat_result.user_id).all():
            if result.student == user:
                r = {}
                r['id'] = result.student.id
                r['result_id'] = result.id
                r['timestamp'] = result.timestamp
                r['1'] = result.q1_score
                r['2'] = result.q2_score
                r['3'] = result.q3_score
                r['4'] = result.q1_score
                r['5'] = result.q1_score
                r['6'] = result.q1_score
                r['7'] = result.q7_score
                r['total'] = result.total_score

                m['results'].append(r)

    return render_template('mat_management_user.html', title='MAT Management:{}'.format(username), mats=data, user=user)


@app.route('/management/mat_management/delete/<id>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def delete_mat_result_confirm(id):
    form = DeleteSub()
    if form.validate_on_submit():
        result = Mat_result.query.filter_by(id=id).first_or_404()
        result.delete()
        flash('MAT result has been deleted.')
        return redirect(url_for('mat_management'))
    return render_template('delete_confirm.html',
                           title='Delete MAT Result',
                           form=form,
                           message="Deleting an MAT result is not recoverable.",
                           back="MAT Management",
                           back_url=url_for('mat_management')
                           )


@app.route('/management/mat_management/availability/<paper_name>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def mat_availability(paper_name):
    paper = Mat.query.filter_by(name=paper_name).first_or_404()
    form = MatForm()
    users = User.query.filter_by(is_admin=False).order_by(User.id).all()
    choices = [(u.id, "{} {}".format(u.firstname, u.lastname)) for u in users]
    form.students.choices = choices
    if request.method == 'GET':
        default = [
            student.id for student in paper.viewers if not student.is_admin]
        form.students.default = default
        form.process()
    if form.validate_on_submit():
        res = form.students.data
        for student in users:
            if student.id in res and paper not in student.mats:
                student.mats.append(paper)
            if student.id not in res and paper in student.mats:
                student.mats.remove(paper)
        db.session.commit()
        return redirect(url_for('mat_management'))
    return render_template('mat_availability.html',
                           title='Set MAT Availability',
                           paper=paper,
                           form=form)


@app.route('/management/mat_management/add_result/<paper_name>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def mat_result_create(paper_name):
    paper = Mat.query.filter_by(name=paper_name).first_or_404()
    users = User.query.filter_by(is_admin=False).order_by(User.id).all()
    choices = [(u.id, "{} {}".format(u.firstname, u.lastname)) for u in users]
    form = MatResultForm()
    form.student.choices = choices
    if form.validate_on_submit() and form.validate():
        student = form.student.data
        user = User.query.filter_by(id=student).first_or_404()
        q1 = form.q1_answers.data
        q2 = form.q2_score.data
        q3 = form.q3_score.data
        q4 = form.q4_score.data
        q5 = form.q5_score.data
        q6 = form.q6_score.data
        q7 = form.q7_score.data
        r = Mat_result()
        paper.results.append(r)
        user.mat_results.append(r)
        r.update_all(q1, q2, q3, q4, q5, q6, q7)
        r.paper_name = paper.name
        db.session.add(r)
        db.session.commit()
        return redirect(url_for('mat_management'))
    return render_template('mat_result_add_edit.html',
                           title='Create an MAT Result',
                           paper=paper,
                           type=1,
                           form=form)


@app.route('/management/mat_management/edit_result/<id>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def mat_result_edit(id):
    result = Mat_result.query.filter_by(id=id).first_or_404()
    paper = result.paper
    user = result.student
    users = User.query.filter_by(is_admin=False).order_by(User.id).all()
    choices = [(u.id, "{} {}".format(u.firstname, u.lastname)) for u in users]
    form = MatResultForm()
    form.student.choices = choices
    if request.method == "GET":
        form.student.default = user.id
        form.q1_answers.default = result.q1_answers
        form.q2_score.default = result.q2_score
        form.q3_score.default = result.q3_score
        form.q4_score.default = result.q4_score
        form.q5_score.default = result.q5_score
        form.q6_score.default = result.q6_score
        form.q7_score.default = result.q7_score
        form.process()
    if request.method == "POST":
        form.student.data = user.id
    if form.validate_on_submit() and form.validate():
        q1 = form.q1_answers.data
        q2 = form.q2_score.data
        q3 = form.q3_score.data
        q4 = form.q4_score.data
        q5 = form.q5_score.data
        q6 = form.q6_score.data
        q7 = form.q7_score.data
        result.update_all(q1, q2, q3, q4, q5, q6, q7)
        db.session.commit()
        return redirect(url_for('mat_management'))
    return render_template('mat_result_add_edit.html',
                           title='Edit an MAT Result',
                           paper=paper,
                           user=user,
                           type=2,
                           form=form)


@app.route('/management/mat_management/add_result/<paper_name>/<username>', methods=['GET', 'POST'])
@login_required
@admin_requirement
def mat_result_create_user(paper_name, username):
    paper = Mat.query.filter_by(name=paper_name).first_or_404()
    user = User.query.filter_by(username=username).first_or_404()
    users = User.query.filter_by(is_admin=False).order_by(User.id).all()
    choices = [(u.id, "{} {}".format(u.firstname, u.lastname)) for u in users]
    form = MatResultForm()
    form.student.choices = choices
    if request.method == "GET":
        form.student.default = user.id
        form.process()
    if request.method == "POST":
        form.student.data = user.id
    if form.validate_on_submit() and form.validate():
        q1 = form.q1_answers.data
        q2 = form.q2_score.data
        q3 = form.q3_score.data
        q4 = form.q4_score.data
        q5 = form.q5_score.data
        q6 = form.q6_score.data
        q7 = form.q7_score.data
        r = Mat_result()
        paper.results.append(r)
        user.mat_results.append(r)
        r.update_all(q1, q2, q3, q4, q5, q6, q7)
        r.paper_name = paper.name
        db.session.add(r)
        db.session.commit()
        return redirect(url_for('mat_management_user', username=user.username))
    return render_template('mat_result_add_edit.html',
                           title='Edit an MAT Result',
                           paper=paper,
                           user=user,
                           type=3,
                           form=form)


@app.route('/ps/review')
@login_required
def ps_review():
    user = current_user
    ps = user.ps_own.order_by(Ps_files.timestamp).all()
    data = []
    for p in ps:
        print(p.file_name)
        data.append(p)

    return render_template('ps_review.html', title='Review My PS', data=data)


@app.route('/management/ps_management/review')
@login_required
@admin_requirement
def ps_management():
    # user = current_user
    users = User.query.filter_by(is_admin=False).order_by(User.id).all()
    data = []
    for u in users:
        d = {}
        d['user'] = u
        d['ps'] = u.ps_own.order_by(Ps_files.timestamp).all()
        data.append(d)

    return render_template('ps_review_all.html', title='Review PS', data=data)


@app.route('/management/ps_management/review/user/<username>')
@login_required
@admin_requirement
def ps_management_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = [user]
    data = []
    for u in users:
        d = {}
        d['user'] = u
        d['ps'] = u.ps_own.order_by(Ps_files.timestamp).all()
        data.append(d)

    return render_template('ps_review_all.html', title='Review PS:{}'.format(username), data=data)


@app.route('/ps/delete/<id>', methods=['GET', 'POST'])
@login_required
def ps_delete(id):
    ps = Ps_files.query.filter_by(id=id).first_or_404()
    if ps.owner == current_user or current_user.is_admin:
        form = DeleteSub()
        if form.validate_on_submit():
            ps.delete()
            flash('PS file {} has been deleted.'.format(ps.file_name))
            return redirect(url_for('ps_review'))
        return render_template('delete_confirm.html',
                               title='Delete PS file {}'.format(ps.file_name),
                               form=form,
                               message="Deleting a PS file is not recoverable.",
                               back="PS Review",
                               back_url=url_for('ps_review')
                               )

    else:
        flash('You have no access to this file.')
        return redirect(url_for('index'))


@app.route('/ps/upload', methods=['GET', 'POST'])
@login_required
def ps_upload():
    user = current_user
    users = User.query.order_by(User.id).all()
    choices = [(u.id, "{} {}".format(u.firstname, u.lastname)) for u in users]
    form = PsUploadForm()
    form.owner.choices = choices
    if request.method == "GET":
        form.owner.default = user.id
        form.process()
    if request.method == "POST":
        form.owner.data = user.id
        print(form.owner.data)
    if form.validate_on_submit():
        f = form.file_upload.data
        filename = secure_filename(f.filename)
        ps = Ps_files.query.filter_by(file_name=filename).first()
        if ps is None:
            f.save(os.path.join(app.instance_path,
                                'protected/files/ps/{}'.format(user.username), filename))
            ps = Ps_files()
            ps.file_name = filename
            user.ps_by_me.append(ps)
            user.ps_own.append(ps)

            db.session.add(ps)
            db.session.commit()
            flash('You have successfully uploaded your PS file {}'.format(filename))
            return redirect(url_for('ps_review'))
        else:
            flash('File name exists, please edit your file name.')
            return redirect(url_for('ps_upload'))
    return render_template('ps_upload.html',
                           title='Upload a PS File',
                           mode=0,
                           user=user,
                           form=form)


@app.route('/management/ps_management/upload', methods=['GET', 'POST'])
@login_required
def ps_upload_general():
    users = User.query.order_by(User.id).all()
    choices = []
    for u in users:
        if u.is_admin:
            choices.append((u.id, "{} {}".format(u.firstname, u.lastname)))
        else:
            choices.append(
                (u.id, "{} {} (stu)".format(u.firstname, u.lastname)))

    form = PsUploadForm()
    form.owner.choices = choices
    if form.validate_on_submit():
        username = form.owner.data
        user = User.query.filter_by(username=username).first_or_404()
        f = form.file_upload.data
        filename = secure_filename(f.filename)
        ps = Ps_files.query.filter_by(file_name=filename).first()
        if ps is None:
            f.save(os.path.join(app.instance_path,
                                'protected/files/ps/{}'.format(user.username), filename))
            ps = Ps_files()
            ps.file_name = filename
            user.ps_by_me.append(ps)
            user.ps_own.append(ps)

            db.session.add(ps)
            db.session.commit()
            flash('You have successfully uploaded your PS file {}'.format(filename))
            return redirect(url_for('ps_review'))
        else:
            flash('File name exists, please edit your file name.')
            return redirect(url_for('ps_upload'))
    return render_template('ps_upload.html',
                           title='Upload a PS File',
                           mode=1,
                           user=current_user,
                           form=form)


@app.route('/management/ps_management/upload/user/<username>', methods=['GET', 'POST'])
@login_required
def ps_upload_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = User.query.order_by(User.id).all()
    choices = [(u.id, "{} {}".format(u.firstname, u.lastname)) for u in users]
    form = PsUploadForm()
    form.owner.choices = choices
    if request.method == "GET":
        form.owner.default = user.id
        form.process()
    if request.method == "POST":
        form.owner.data = user.id
        print(form.owner.data)
    if form.validate_on_submit():
        f = form.file_upload.data
        filename = secure_filename(f.filename)
        ps = Ps_files.query.filter_by(file_name=filename).first()
        if ps is None:
            f.save(os.path.join(app.instance_path,
                                'protected/files/ps/{}'.format(user.username), filename))
            ps = Ps_files()
            ps.file_name = filename
            user.ps_by_me.append(ps)
            user.ps_own.append(ps)

            db.session.add(ps)
            db.session.commit()
            flash('You have successfully uploaded your PS file {}'.format(filename))
            return redirect(url_for('ps_review'))
        else:
            flash('File name exists, please edit your file name.')
            return redirect(url_for('ps_upload'))
    return render_template('ps_upload.html',
                           title='Upload a PS File for {}'.format(username),
                           mode=2,
                           user=user,
                           form=form)




@app.route('/about_me')
def about_me():
    return render_template('about.html', title='About Me')


@app.route('/information')
def information():
    return render_template('information.html', title='Course Information')

@app.route('/course_materials/math')
@login_required
def math():
    return render_template('not_available.html', title='Course Materials - Mathematics')


@app.route('/course_materials/logic')
@login_required
def logic():
    return render_template('not_available.html', title='Course Materials - Logics')


@app.route('/course_materials/cs')
@login_required
def cs():
    return render_template('not_available.html', title='Course Materials - Computer Science')




@app.route('/course_materials/others')
@login_required
def others():
    return render_template('not_available.html', title='Course Materials - Others')

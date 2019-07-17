from app import db, login, app
# Flask-Login user mixin class
from flask_login import UserMixin
# timestamp
from datetime import datetime
# password validation - hashing
from werkzeug.security import generate_password_hash, check_password_hash


import os

# Association for User-Mat many to many relationship
user_mat_association = db.Table('UserMat',
                                db.metadata,
                                db.Column('user_id',
                                          db.Integer,
                                          db.ForeignKey('user.id')
                                          ),
                                db.Column('mat_name',
                                          db.String(20),
                                          db.ForeignKey('mat.name')
                                          )
                                )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    firstname = db.Column(db.String(64), index=True)
    lastname = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    # one-many relationship. put relationship on the "one" side
    # u.posts.all() can be used to query all posts by a user
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    mats = db.relationship('Mat', secondary=user_mat_association,
                           back_populates='viewers')
    mat_results = db.relationship(
        'Mat_result', backref='student', lazy='dynamic')
    ps_own = db.relationship("Ps_files", backref='owner', lazy='dynamic',
                             foreign_keys='Ps_files.user_id_owner')
    ps_by_me = db.relationship("Ps_files", backref='author',
                               lazy='dynamic', foreign_keys='Ps_files.user_id_author')

    def __repr__(self):
        return '<User {}, {} {}>'.format(self.username, self.firstname, self.lastname)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def post(self, message):
        p = Post(body=message, user_id=self.id, author=self)
        db.session.add(p)
        db.session.commit()

    def set_admin(self):
        self.is_admin = True
        db.session.commit()

    def disable_admin(self):
        self.is_admin = False
        db.session.commit()

    def change_admin(self):
        if self.is_admin:
            self.disable_admin()
        else:
            self.set_admin()

    def delete(self):
        self.delete_posts()
        self.delete_mat_scores()
        db.session.delete(self)
        db.session.commit()

    def delete_ps(self):
        for ps in self.ps_own:
            ps.delete()
        for ps in self.ps_by_me:
            ps.delete()

    def delete_posts(self):
        for p in self.posts:
            p.delete()

    def delete_mat_scores(self):
        for m in self.mat_results:
            m.delete()

    def add_mat_name(self, paper_name):
        assert(isinstance(paper_name, str))
        papers = Mat.query.filter(Mat.name.contains(paper_name))
        for paper in papers:
            self.add_mat(paper)

    def add_mat(self, paper):
        if paper not in self.mats:
            self.mats.append(paper)
            db.session.commit()

    def remove_mat_name(self, paper_name):
        assert(isinstance(paper_name, str))
        papers = Mat.query.filter(Mat.name.contains(paper_name))
        for paper in papers:
            self.remove_mat(paper)

    def remove_mat(self, paper):
        if paper in self.mats:
            self.mats.remove(paper)
            db.session.commit()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # foreign key referenced to user.id
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return '<Post "{}" by: {}>'.format(self.body, self.author.username)


# mat data
class Mat(db.Model):
    name = db.Column(db.String(20), primary_key=True)
    paper_path = db.Column(db.String(128))
    answer_path = db.Column(db.String(128))
    viewers = db.relationship('User', secondary=user_mat_association,
                              back_populates='mats')
    results = db.relationship('Mat_result', backref='paper', lazy='dynamic',
                              foreign_keys='Mat_result.mat_name')
    correct_answer = db.Column(db.String(10))

    def __repr__(self):
        return '<MAT Paper {}>'.format(self.name)

    def get_dict(self):
        res = {}
        res['name'] = self.name
        res['paper_path'] = self.paper_path
        res['answer_path'] = self.answer_path
        return res


class Mat_result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mat_name = db.Column(db.String(20), db.ForeignKey('mat.name'))
    q1_answers = db.Column(db.String(10), default="ffffffffff")
    q1_score = db.Column(db.Integer, default=0)
    q2_score = db.Column(db.Integer, default=0)
    q3_score = db.Column(db.Integer, default=0)
    q4_score = db.Column(db.Integer, default=0)
    q5_score = db.Column(db.Integer, default=0)
    q6_score = db.Column(db.Integer, default=0)
    q7_score = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0, index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    __table_args__ = (
        db.CheckConstraint(db.and_(q1_score >= 0, q1_score <= 40)),
        db.CheckConstraint(db.and_(q2_score >= 0, q2_score <= 40)),
        db.CheckConstraint(db.and_(q3_score >= 0, q3_score <= 40)),
        db.CheckConstraint(db.and_(q4_score >= 0, q4_score <= 40)),
        db.CheckConstraint(db.and_(q5_score >= 0, q5_score <= 40)),
        db.CheckConstraint(db.and_(q6_score >= 0, q6_score <= 40)),
        db.CheckConstraint(db.and_(q7_score >= 0, q7_score <= 40)),
        db.CheckConstraint(
            'total_score = q1_score + q2_score + q3_score + q4_score + q5_score + q6_score + q7_score', name="TotalScoreCheck")
    )

    def __repr__(self):
        return ('<User> {} <Paper> {} <Score> {}'.format(self.student, self.paper.name, self.total_score))

    def choose_paper(self, paper, user):
        if isinstance(paper, Mat):
            self.mat_name = paper.name
            paper.results.append(self)
            user.mat_results.append(self)
            db.session.commit()
        else:
            print("Please input a valid paper, or use 'choose_paper_name' method.")

    def choose_paper_name(self, name, username):
        paper = Mat.query.filter_by(name=name).first()
        user = User.query.filter_by(username=username)
        if paper is not None:
            if user is not None:
                self.choose_paper(paper, user)
            else:
                print("Please input a valid username.")
        else:
            print("Please input a valid paper name.")

    def update_q1_answer(self, answer):
        assert(isinstance(answer, str))
        v = answer.strip()
        assert(len(v) == 10)
        self.q1_answers = v
        db.session.commit()
        score = 4*sum(self.get_correct_q1_answer())
        self.update_score_back(1, score)

    def update_all(self, q1, q2, q3, q4, q5, q6, q7):
        self.update_q1_answer(str(q1))
        self.update_score(2, int(q2))
        self.update_score(3, int(q3))
        self.update_score(4, int(q4))
        self.update_score(5, int(q5))
        self.update_score(6, int(q6))
        self.update_score(7, int(q7))

    def update_score(self, n, score):
        assert(isinstance(n, int) and n > 1 and n < 8)
        self.update_score_back(n, score)

    def update_score_back(self, n, score):
        if n == 1:
            prev_score = self.q1_score
            self.q1_score = score
        elif n == 2:
            prev_score = self.q2_score
            self.q2_score = score
        elif n == 3:
            prev_score = self.q3_score
            self.q3_score = score
        elif n == 4:
            prev_score = self.q4_score
            self.q4_score = score
        elif n == 5:
            prev_score = self.q5_score
            self.q5_score = score
        elif n == 6:
            prev_score = self.q6_score
            self.q6_score = score
        elif n == 7:
            prev_score = self.q7_score
            self.q7_score = score
        self.total_score -= prev_score
        self.total_score += score
        db.session.commit()

    def get_correct_q1_answer(self):
        res = []
        for i in range(10):
            if self.q1_answers[i].lower() == self.paper.correct_answer[i].lower():
                res.append(1)
            else:
                res.append(0)
        print(res)
        return res

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Ps_files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # foreign key referenced to user.id
    user_id_owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_id_author = db.Column(db.Integer, db.ForeignKey('user.id'))
    file_name = db.Column(db.String(50), index=True)

    def delete(self):
        if self.owner is not None and self.file_name is not None:
            path = os.path.join(app.instance_path, 'protected/files/ps/{}/{}'.format(self.owner.username,
                                                                                     self.file_name))

            try:
                os.remove(path)
            except FileNotFoundError:
                print('File not found')

        db.session.delete(self)
        db.session.commit()

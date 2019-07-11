from app import db, login
# Flask-Login user mixin class
from flask_login import UserMixin
# timestamp
from datetime import datetime
# password validation - hashing
from werkzeug.security import generate_password_hash, check_password_hash


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


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # foreign key referenced to user.id
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post "{}" by: {}>'.format(self.body, self.author.username)


# mat data


class Mat(db.Model):
    name = db.Column(db.String(20), primary_key=True)
    paper_path = db.Column(db.String(128))
    answer_path = db.Column(db.String(128))

    def __repr__(self):
        return '<MAT Paper {}>'.format(self.name)

    def get_dict(self):
        res = {}
        res['name'] = self.name
        res['paper_path'] = self.paper_path
        res['answer_path'] = self.answer_path
        return res

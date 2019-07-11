#forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, AnyOf
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class PostForm(FlaskForm):
    post = StringField('Message', validators=[DataRequired(), Length(max=1000,
        message='Messages may not contain more than 1000 characters.')])
    submit = SubmitField('Submit')

class DeleteUserSub(FlaskForm):
    confirm = StringField("Type in 'DELETE' to confirm.", validators=[DataRequired(), AnyOf(['DELETE'])])
    submit = SubmitField('Confirm')

class DeletePostSub(FlaskForm):
    submit = SubmitField('Confirm')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
        Length(max=64)])
    firstname = StringField('First Name', validators=[DataRequired(),
        Length(max=64)])
    lastname = StringField('Last Name', validators=[DataRequired(),
        Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(),
        Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

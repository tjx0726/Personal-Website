# forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, AnyOf, Optional, Regexp
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


class DeleteSub(FlaskForm):
    confirm = StringField("Type in 'DELETE' to confirm.", validators=[
                          DataRequired(), AnyOf(['DELETE'])])
    submit = SubmitField('Confirm')


class MatResultForm(FlaskForm):
    student = SelectField('Select a Student', coerce=int,
                          validators=[DataRequired()])
    q1_answers = StringField('Q1 Answers (Input letters only. "f" for empty)',
                            validators=[DataRequired(), Regexp(regex='^[A-Fa-f]{10}$',
                                                               message="Number of answers is incorrect or you have entered aletter not from a to f.")],
                            default='ffffffffff')
    q2_score = StringField('Q2 Score', validators=[DataRequired()], default=0)
    q3_score = StringField('Q3 Score', validators=[DataRequired()], default=0)
    q4_score = StringField('Q4 Score', validators=[DataRequired()], default=0)
    q5_score = StringField('Q5 Score', validators=[DataRequired()], default=0)
    q6_score = StringField('Q6 Score', validators=[DataRequired()], default=0)
    q7_score = StringField('Q7 Score', validators=[DataRequired()], default=0)
    submit = SubmitField('Submit')

    def __init__(self):
        FlaskForm.__init__(self)

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        res = True
        for v in [self.q2_score, self.q3_score, self.q4_score, self.q5_score, self.q6_score, self.q7_score]:
            res = res and self.validate_one(v)
        return res

    def validate_one(self, v):
        try:
            int(v.data)
        except ValueError:
            v.errors.append('Score must be a valid integer.')
            return False
        if 0 <= int(v.data) <= 15:
            return True
        else:
            v.errors.append('Score must be in the range 0-15.')
            return False


class MatForm(FlaskForm):
    students = SelectMultipleField(
        'Select Students', coerce=int, validators=[Optional()])
    submit = SubmitField('Submit')


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

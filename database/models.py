from wtforms import SubmitField
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from database import db


class User(db.Document):
   email = db.StringField()
   password = db.StringField()


class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired()])
    password = StringField('password',validators=[DataRequired()])
    submit = SubmitField("Login")
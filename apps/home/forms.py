from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import Email, DataRequired


class LoginForm(FlaskForm):
    username = StringField("Username", id="username_login", validators=[DataRequired()])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])
    remember_me = BooleanField("Keep me checked in", id="remember_me")


class SearchForm(FlaskForm):
    search_query = StringField("Search", validators=[DataRequired()])
    submit = SubmitField("Search")


class CreateAccountForm(FlaskForm):
    first_name = StringField("First name", id="first_name", validators=[DataRequired()])
    last_name = StringField("Last name", id="last_name", validators=[DataRequired()])
    username = StringField(
        "Username", id="username_create", validators=[DataRequired()]
    )
    email = EmailField(
        "Email", id="email_create", validators=[DataRequired(), Email()]
    )
    confirm_email = EmailField(
        "Confirm email", id="confirm_email", validators=[DataRequired(), Email()]
    )
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", id="confirm_password", validators=[DataRequired()]
    )
    term_agreement = BooleanField("Agreement", id="term_agreement")
    submit = SubmitField("Register")

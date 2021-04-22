from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email


# WTForm
class RegisterForm(FlaskForm):
    style = {'class': 'ourClasses', 'style': 'margin: 1%; font-family: "DM Serif Display", serif; font-weight: 400;'}
    username = StringField("Name", validators=[DataRequired()], render_kw=style)
    email = StringField("E-Mail", validators=[DataRequired(), Email()], render_kw=style)
    password = PasswordField("Password", validators=[DataRequired()], render_kw=style)
    submit = SubmitField("REGISTER", render_kw=style)


class LoginForm(FlaskForm):
    style = {'class': 'ourClasses', 'style': 'margin: 1%; font-family: "DM Serif Display", serif; font-weight: 400;'}
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw=style)
    password = PasswordField("Password", validators=[DataRequired()], render_kw=style)
    submit = SubmitField("LOG IN!", render_kw=style)


class AddNewTagForm(FlaskForm):
    style = {'class': 'ourClasses', 'style': 'margin: 1%; font-family: "DM Serif Display", serif; font-weight: 400;'}
    tag_name = StringField("Tag Name", validators=[DataRequired()], render_kw=style)
    submit = SubmitField("ADD TAG", render_kw=style)


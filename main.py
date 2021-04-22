from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_required, LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from typing import Callable
from forms import LoginForm, RegisterForm, AddNewTagForm
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
# CONNECT TO DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)


class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    Integer: Callable
    String: Callable
    Boolean: Callable
    Date: Callable
    relationship: Callable
    ForeignKey: Callable
    Table: Callable
    backref: Callable


db = MySQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


association_table = db.Table('association',
                             db.Column('users_id', db.Integer, db.ForeignKey('users.id')),
                             db.Column('tags_id', db.Integer, db.ForeignKey('tags.id'))
                             )


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False, unique=True)

    # one to many relationship from User to Task
    tasks = relationship("Task", cascade="all,delete", backref="creator", lazy=True)

    # many to many relationship from User to Tag
    # the backref acts as if it is creating the subscribers attribute in the Tag class.
    subscriptions = db.relationship("Tag", secondary="association", backref=db.backref("subscribers", lazy="dynamic"))


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    due_date = db.Column(db.Date)
    progress = db.Column(db.Boolean, nullable=False)
    date_created = db.Column(db.Date, nullable=False)

    # creating the CHILD RELATIONSHIP with users table
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # creating the CHILD RELATIONSHIP with the tags table
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"))


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String, nullable=False, unique=True)

    # creating a PARENT RELATIONSHIP with tasks table:  1 --> many
    tasks = relationship("Task", cascade="all,delete", backref="task_tag", lazy=True)

    def __repr__(self):
        return f'{self.tag_name}'


# db.create_all()


class NewTaskForm(FlaskForm):
    style = {'class': 'ourClasses', 'style': 'margin: 1%; font-family: "DM Serif Display", serif; font-weight: 400;'}

    title = StringField("Task Name", validators=[DataRequired()], render_kw=style)
    description = StringField("Description", render_kw=style)
    due_date = DateField("Due Date", format='%Y-%m-%d', render_kw={'placeholder': '2021/04/18 for April 18, 2021'})
    tag = SelectField("Choose Tag", validators=[DataRequired()], render_kw=style)
    # date_created and progress is automatically generated
    submit = SubmitField("ADD", render_kw=style)


@app.route("/")
def home():
    print(current_user)
    return render_template("index.html", current_user=current_user)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        person = User.query.filter_by(email=form.email.data).first()
        if person is None:
            flash("This email has not been registered yet, please register first.")
            return redirect(url_for("register"))
        else:
            if check_password_hash(person.password, form.password.data):
                login_user(person)
                # flash("Logged in successfully.")
            else:
                flash("Your password is incorrect. Please try again.")
                return redirect(url_for("login"))
            return redirect(url_for("show_dashboard", username=current_user.username))
    return render_template("login.html", form=form, current_user=current_user)


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        print(User.query.filter_by(email=form.email.data).first())
        if User.query.filter_by(email=form.email.data).first() is None:
            hashed_password = generate_password_hash(form.password.data, "pbkdf2:sha256", 10)
            new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            # flash("Registered successfully!")
            return redirect(url_for("show_dashboard", username=current_user.username))
        flash("This email has already been registered. Please sign in.")
        return redirect(url_for("login"))
    return render_template("register.html", form=form, current_user=current_user)


# TASK RELATED FUNCTIONS
@app.route("/add-task", methods=["POST", "GET"])
@login_required
def add_task():
    form = NewTaskForm()
    form.tag.choices = [x for x in current_user.subscriptions]
    if form.validate_on_submit():
        tag = Tag.query.filter_by(tag_name=form.tag.data).first()
        new_task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            progress=False,
            date_created=datetime.date.today(),
            creator_id=current_user.id,
            tag_id=tag.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("show_dashboard", username=current_user.username))
    return render_template("add_task.html", form=form, current_user=current_user, is_edit=False)


@app.route("/delete-task/<int:task_id>")
@login_required
def delete_task(task_id):
    the_task = Task.query.get(task_id)
    db.session.delete(the_task)
    db.session.commit()
    return redirect(url_for("show_dashboard", username=current_user.username))


@app.route("/edit-task/<int:task_id>", methods=["POST", "GET"])
@login_required
def edit_task(task_id):
    the_task = Task.query.get(task_id)
    edit_form = NewTaskForm(
        title=the_task.title,
        description=the_task.description,
        due_date=the_task.due_date,
        tag=Tag.query.filter_by(id=the_task.tag_id).first()
    )
    edit_form.tag.choices = [x for x in current_user.subscriptions]
    if edit_form.validate_on_submit():
        new_tag = Tag.query.filter_by(tag_name=edit_form.tag.data.title()).first()

        the_task.title = edit_form.title.data
        the_task.description = edit_form.description.data
        the_task.due_date = edit_form.due_date.data
        the_task.tag_id = new_tag.id

        db.session.commit()
        return redirect(url_for("show_dashboard", username=current_user.username))
    return render_template("add_task.html", form=edit_form, current_user=current_user, is_edit=True)


@app.route("/done/<int:task_id>")
@login_required
def done(task_id):
    the_task = Task.query.get(task_id)
    if the_task.progress == 0:
        the_task.progress = 1
    else:
        the_task.progress = 0
    db.session.commit()
    return redirect(url_for("show_dashboard", username=current_user.username))


# TAG RELATED FUNCTIONS
@app.route("/new-board", methods=["POST", "GET"])
@login_required
def add_new_tag():
    form = AddNewTagForm()
    if form.validate_on_submit():
        if Tag.query.filter_by(tag_name=form.tag_name.data.title()).first() is None:
            # the given tag does not exist in the tags table.
            the_tag = Tag(tag_name=form.tag_name.data.title())

            the_tag.subscribers.append(current_user)
            db.session.add(the_tag)

        else:
            # the given tag exists in the tags table but have not been subscribed by the user yet.
            the_tag = Tag.query.filter_by(tag_name=form.tag_name.data.title()).first()
            the_tag.subscribers.append(current_user)

        db.session.commit()
        # creating a default task
        default_task = Task(title="New Task",
                            description="Add a new task to your new board.",
                            date_created=datetime.date.today(),
                            progress=False,
                            creator_id=current_user.id,
                            tag_id=the_tag.id)
        db.session.add(default_task)
        db.session.commit()
        return redirect(url_for("show_dashboard", username=current_user.username))
    return render_template("newtag.html", current_user=current_user, form=form)


@app.route("/delete-board-<int:tag_id>")
@login_required
def delete_tag(tag_id):
    the_tag = Tag.query.get(tag_id)
    user_tasks = Task.query.filter_by(creator_id=current_user.id).all()
    for task in user_tasks:
        if task.tag_id == the_tag.id:
            db.session.delete(task)
            db.session.commit()

    current_user.subscriptions.remove(the_tag)
    db.session.commit()
    return redirect(url_for("show_dashboard", username=current_user.username))


@app.route("/dashboard/<username>")
@login_required
def show_dashboard(username):
    user_tasks = Task.query.filter_by(creator_id=current_user.id).all()
    user_tags = []
    for tag in Tag.query.all():
        if current_user in tag.subscribers:
            user_tags.append(tag)

    return render_template("dashboard-real.html", current_user=current_user, user_tasks=user_tasks, tags=user_tags)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home", current_user=current_user))


if __name__ == "__main__":
    app.run(debug=True)


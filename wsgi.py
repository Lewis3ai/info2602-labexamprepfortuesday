import click, csv
from flask import Flask
from flask_migrate import Migrate
from flask.cli import with_appcontext
from App import app, initialize_db
from App.models import db, User


# Initialize Flask-Migrate
migrate = Migrate(app, db)

@app.cli.command("init")
def initialize():
  initialize_db()


@app.cli.command("create-user")
@click.argument("username")
@click.argument("password")
def create_user_command(username, password):
    """Create a new user.""" 
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    print(f"User {username} created successfully.")

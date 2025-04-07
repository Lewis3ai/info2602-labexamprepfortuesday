import click, csv
from flask import Flask
from flask.cli import with_appcontext
from App import app, initialize_db


@app.cli.command("init")
def initialize():
  initialize_db()


@app.cli.command("create-user")
@click.argument("username")
@click.argument("password")
def create_user_command(username, password):
    newuser = User(username=username, password=password)
    db.session.add(newuser)
    db.session.commit()
    print(f'{username} created!')

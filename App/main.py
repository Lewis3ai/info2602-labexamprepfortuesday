import os, csv
from flask import Flask, redirect, render_template, request, flash, url_for
from sqlalchemy.exc import IntegrityError
from App.models import db, User, Student, Course, StudentCourse
from datetime import timedelta
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    current_user,
    set_access_cookies,
    unset_jwt_cookies,
)


def create_app():
  app = Flask(__name__, static_url_path='/static')
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  app.config['TEMPLATES_AUTO_RELOAD'] = True
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
  app.config['DEBUG'] = True
  app.config['SECRET_KEY'] = 'MySecretKey'
  app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
  app.config["JWT_COOKIE_SECURE"] = False
  app.config["JWT_SECRET_KEY"] = "super-secret"
  app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

  app.app_context().push()
  return app

app = create_app()
db.init_app(app)
jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user): return user
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data): return User.query.get(jwt_data["sub"])
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
  flash("Your session has expired. Please log in again.")
  return redirect(url_for('login'))

def parse_students():
  with open('students.csv', mode='r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
      student = Student(id=row['ID'],
                        first_name=row['FirstName'],
                        image=row['Picture'],
                        last_name=row['LastName'],
                        programme=row['Programme'],
                        start_year=row['YearStarted'])
      db.session.add(student)
    db.session.commit()

def create_users():
  db.session.add_all([
    User(username="rob", password="robpass"),
    User(username="bob", password="bobpass")
  ])
  db.session.commit()

def create_courses():
  db.session.add_all([
    Course(code="INFO1601", name="Intro To WWW Programming"),
    Course(code="INFO2602", name="Web Programming & Technologies 1"),
    Course(code="INFO1600", name="IT Concepts"),
    Course(code="COMP2605", name="Database Management Systems")
  ])
  db.session.commit()

def initialize_db():
  db.drop_all()
  db.create_all()
  create_users()
  create_courses()
  parse_students()
  print('database initialized')

@app.route('/')
def login():
  return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_action():
  username = request.form.get('username')
  password = request.form.get('password')
  user = User.query.filter_by(username=username).first()
  if user and user.check_password(password):
    response = redirect(url_for('home'))
    access_token = create_access_token(identity=user.id)
    set_access_cookies(response, access_token)
    return response
  else:
    flash('Invalid username or password')
    return redirect(url_for('login'))

@app.route('/app')
@app.route('/app/<code>')
@jwt_required()
def home(code="INFO1601"):
  selected_course = Course.query.get(code)
  if not selected_course:
    flash("Invalid course code.")
    return redirect(url_for('home'))

  all_courses = Course.query.all()
  students_in_course = selected_course.students
  students_not_in_course = Student.query.filter(~Student.courses.any(code=code)).all()

  return render_template(
    'index.html',
    user=current_user,
    course=selected_course,
    students_in=students_in_course,
    students_out=students_not_in_course,
    all_courses=all_courses
  )

@app.route('/add_student/<student_id>/<course_code>')
@jwt_required()
def add_student(student_id, course_code):
  student = Student.query.get(student_id)
  course = Course.query.get(course_code)
  if student and course:
    course.students.append(student)
    db.session.commit()
  return redirect(url_for('home', code=course_code))

@app.route('/remove_student/<student_id>/<course_code>')
@jwt_required()
def remove_student(student_id, course_code):
  student = Student.query.get(student_id)
  course = Course.query.get(course_code)
  if student and course:
    course.students.remove(student)
    db.session.commit()
  return redirect(url_for('home', code=course_code))

@app.route('/logout')
def logout():
  response = redirect(url_for('login'))
  unset_jwt_cookies(response)
  flash('Logged out')
  return response

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
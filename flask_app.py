import enum
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = 
"mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="PowerSl1d3",
    password="H1l6KWq8N1",
    hostname="PowerSl1d3.mysql.pythonanywhere-services.com",
    databasename="PowerSl1d3$default",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class VisitorType(enum.Enum):
    incoming = 1
    leaving = 2

class Visitor(db.Model):

    __tablname__ = "visitor"

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=db.func.now())
    visitor_type = db.Column(Enum(VisitorType))


class Admins(db.Model):

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), unique=True, nullable=False)


trusted_devices = ['1322']
current_delay = 1000

def time_to_str(time) -> str:
    return (str(time.year) + '-' + str(time.month) + '-' + str(time.day) +
    'T' + str(time.hour) + ':' + str(time.minute) + ':' + 
str(time.second))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Signup', methods=["POST"])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    result = Admins.query.filter_by(username=username, 
password=password).first()
    if result:
        return redirect(url_for('people_per_day'))
    else:
        return render_template('error_auth.html')

@app.route('/IncomingVisitor')
def incoming_visitor():
    if str(request.headers.get('Magic-Number')) in trusted_devices:
        income_visitor = Visitor(
            time=db.func.current_timestamp(),
            visitor_type = VisitorType.incoming
        )
        db.session.add(income_visitor)
        db.session.commit()
        return f"Successfull add new visitor! {Visitor.query.count()}"
    else:
        return "Bad device!"

@app.route('/LeavingVisitor')
def leaving_visitor():
    if str(request.headers.get('Magic-Number')) in trusted_devices:
        leaving_visitor = Visitor(
            time=db.func.current_timestamp(),
            visitor_type = VisitorType.leaving)
        db.session.add(leaving_visitor)
        db.session.commit()
        return f"Successfull add new leaving visitor! 
{Visitor.query.count()}"
    else:
        return "Bad device!"

def get_day_income_people(visitor_type: VisitorType):
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    return Visitor.query.filter(
        (Visitor.time > day_ago) &
        (Visitor.visitor_type == visitor_type)
    ).count()


def get_mean_people_per_timedelta(timedelta_: int):

    mean_people_per_timedelta = 0
    incoming_people_per_timedelta = []
    leaving_people_per_timedelta = []
    first_day = datetime.now()
    second_day = first_day - timedelta(days=1)

    for i in range(timedelta_):
        mean_people_per_timedelta += Visitor.query.filter(
            (Visitor.time > second_day) &
            (Visitor.time < first_day) &
            (Visitor.visitor_type == VisitorType.incoming)
        ).count()
        incoming_people_per_timedelta.append(Visitor.query.filter(
            (Visitor.time > second_day) &
            (Visitor.time < first_day) &
            (Visitor.visitor_type == VisitorType.incoming)
        ).count())
        leaving_people_per_timedelta.append(Visitor.query.filter(
            (Visitor.time > second_day) &
            (Visitor.time < first_day) &
            (Visitor.visitor_type == VisitorType.leaving)
        ).count())
        first_day -= timedelta(days=1)
        second_day -= timedelta(days=1)

    mean_people_per_timedelta /= timedelta_

    return mean_people_per_timedelta, incoming_people_per_timedelta, 
leaving_people_per_timedelta


@app.route('/PeoplePerDay')
def people_per_day():
    global current_delay

    day_income_people = get_day_income_people(VisitorType.incoming)
    day_leave_people = get_day_income_people(VisitorType.leaving)

    (
        mean_people_per_week,
        incoming_people_per_week,
        leaving_people_per_week
    ) = get_mean_people_per_timedelta(7)

    (
        mean_people_per_month,
        day_incoming,
        day_leaving
    ) = get_mean_people_per_timedelta(30)

    incoming_visitors = dict()
    for visitor in Visitor.query.filter(
        Visitor.visitor_type == VisitorType.incoming
        ).all():
        incoming_visitors[visitor.id] = time_to_str(visitor.time)

    leaving_visitors = dict()
    for visitor in Visitor.query.filter(
        Visitor.visitor_type == VisitorType.leaving
        ).all():
        leaving_visitors[visitor.id] = time_to_str(visitor.time)

    return render_template("moderate.html",
    mean_people_per_week=mean_people_per_week,
    mean_people_per_month=mean_people_per_month,
    day_income_people=day_income_people,
    day_leave_people=day_leave_people,
    incoming_people_per_week=enumerate(incoming_people_per_week),
    leaving_people_per_week=leaving_people_per_week,
    day_incoming=enumerate(day_incoming),
    day_leaving=enumerate(day_leaving),
    incoming_visitors=incoming_visitors,
    leaving_visitors=leaving_visitors,
    delay=current_delay)

@app.route('/DeleteIncomingVisitor', methods=["POST"])
def delete_incoming_visitor():
    id = int(request.args.get('id'))
    Visitor.query.filter(
        (Visitor.id == id) &
        (Visitor.visitor_type == VisitorType.incoming)
    ).delete()
    db.session.commit()
    return redirect(url_for('people_per_day'))

@app.route('/DeleteLeavingVisitor', methods=["POST"])
def delete_leaving_visitor():
    id = int(request.args.get('id'))
    Visitor.query.filter(
        (Visitor.id == id) &
        (Visitor.visitor_type == VisitorType.leaving)
    ).delete()
    db.session.commit()
    return redirect(url_for('people_per_day'))

@app.route('/SetDelay', methods=["GET"])
def set_delay():
    global current_delay
    current_delay = int(request.args.get('delay'))
    return redirect(url_for('people_per_day'))

@app.route('/GetDelay')
def get_delay():
    return str(current_delay);

@app.route('/Test')
def test():
    return str(request.headers.get('Magic-Number'))

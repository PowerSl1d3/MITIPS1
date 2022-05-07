from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
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

class IncomingVisitor(db.Model):

    __tablename__ = "incoming_visitor"

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=db.func.now())


class LeavingVisitor(db.Model):

    __tablename__ = "leaving_visitor"

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=db.func.now())


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
        income_visitor = IncomingVisitor(time=db.func.current_timestamp())
        db.session.add(income_visitor)
        db.session.commit()
        return f"Successfull add new visitor! 
{IncomingVisitor.query.count()}"
    else:
        return "Bad device!"

@app.route('/LeavingVisitor')
def leaving_visitor():
    if str(request.headers.get('Magic-Number')) in trusted_devices:
        leaving_visit = LeavingVisitor(time=db.func.current_timestamp())
        db.session.add(leaving_visit)
        db.session.commit()
        return f"Successfull add new leaving visitor! 
{LeavingVisitor.query.count()}"
    else:
        return "Bad device!"

@app.route('/IncomingVisitorLastMounth')
def ivlm():
    #result = db.engine.execute("SELECT * FROM incoming_visitor WHERE time 
BETWEEN NOW() - INTERVAL 30 DAY AND NOW()")
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)

    # return all users created less then 2 hours ago
    result = IncomingVisitor.query.filter(IncomingVisitor.time > 
two_hours_ago).all()
    #ids = [row[0] for row in result]
    return str(result[0].time.minute)

@app.route('/PeoplePerDay')
def people_per_day():
    global current_delay
    now = datetime.now()
    day_ago = now - timedelta(days=1)

    day_income_people = IncomingVisitor.query.filter(IncomingVisitor.time 
> day_ago).count()
    day_leave_people = LeavingVisitor.query.filter(LeavingVisitor.time > 
day_ago).count()

    mean_people_per_week = 0
    incoming_people_per_week = []
    leaving_people_per_week = []
    first_day = datetime.now()
    second_day = now - timedelta(days=1)

    for i in range(7):
        mean_people_per_week += 
IncomingVisitor.query.filter((IncomingVisitor.time > second_day) & 
(IncomingVisitor.time < first_day)).count()
        
incoming_people_per_week.append(IncomingVisitor.query.filter((IncomingVisitor.time 
> second_day) & (IncomingVisitor.time < first_day)).count())
        
leaving_people_per_week.append(LeavingVisitor.query.filter((LeavingVisitor.time 
> second_day) & (LeavingVisitor.time < first_day)).count())
        first_day -= timedelta(days=1)
        second_day -= timedelta(days=1)

    mean_people_per_week /= 7


    mean_people_per_month = 0
    day_incoming = []
    day_leaving = []
    first_day = datetime.now()
    second_day = now - timedelta(days=1)

    for i in range(30):
        people_per_prev_day = 
IncomingVisitor.query.filter((IncomingVisitor.time > second_day) & 
(IncomingVisitor.time < first_day)).count()
        mean_people_per_month += people_per_prev_day
        day_incoming.append(people_per_prev_day)
        
day_leaving.append(LeavingVisitor.query.filter((LeavingVisitor.time > 
second_day) & (LeavingVisitor.time < first_day)).count())
        first_day -= timedelta(days=1)
        second_day -= timedelta(days=1)

    mean_people_per_month /= 30

    incoming_visitors = dict()
    for visitor in IncomingVisitor.query.all():
        incoming_visitors[visitor.id] = time_to_str(visitor.time)

    leaving_visitors = dict()
    for visitor in LeavingVisitor.query.all():
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
    IncomingVisitor.query.filter(IncomingVisitor.id == id).delete()
    db.session.commit()
    return redirect(url_for('people_per_day'))

@app.route('/DeleteLeavingVisitor', methods=["POST"])
def delete_leaving_visitor():
    id = int(request.args.get('id'))
    LeavingVisitor.query.filter(LeavingVisitor.id == id).delete()
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


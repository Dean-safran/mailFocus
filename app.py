from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# configurations
# --------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mailfocus.db"
# instantiate database manager
db = SQLAlchemy()
# tell db manager about our app's db
db.init_app(app)

# create email table model
class Email(db.Model) :
    id = db.Column(db.Integer, primary_key=True)

    sender = db.Column(
        db.String(255),
        nullable=False
    )

    subject = db.Column(
        db.String(500),
        nullable=False
    )

    snippet = db.Column(
        db.Text,
        nullable=False,
        default=""
    )

    priority = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Review"
    )

    reason = db.Column(
        db.Text,
        nullable=False,
        default=""
    )
    
    gmail_thread_id = db.Column(
        db.String(255),
        unique=True,
        nullable=True
    )
    
    received_at = db.Column(
        db.DateTime,
        nullable=True
    )

emails = [
    {
        "sender": "Professor Smith",
        "subject": "Please send your project",
        "snippet": "Could you please send me your project before Friday?",
        "priority": 90,
        "status": "Needs Reply",
        "reason": "Contains a direct request and a deadline.",
        "gmail_thread_id": "fake-thread-1",
        "received_at": datetime(2026, 7, 15, 9, 30)
    },
    {
        "sender": "GitHub",
        "subject": "New login detected",
        "snippet": "We noticed a new login to your GitHub account.",
        "priority": 60,
        "status": "Review",
        "reason": "Security notification that should be reviewed.",
        "gmail_thread_id": "fake-thread-2",
        "received_at": datetime(2026, 7, 14, 14, 15),
    },
    {
        "sender": "Clothing Store",
        "subject": "20% off today",
        "snippet": "Shop today and receive 20% off your order.",
        "priority": 10,
        "status": "No Action",
        "reason": "Promotional email with no required action.",
        "gmail_thread_id": "fake-thread-3",
        "received_at": datetime(2026, 7, 13, 11, 0),
    },
    {
        "sender": "Career Center",
        "subject": "Internship application deadline",
        "snippet": "Please submit your application by Monday.",
        "priority": 80,
        "status": "Needs Reply",
        "reason": "Contains a request with an upcoming deadline.",
        "gmail_thread_id": "fake-thread-4",
        "received_at": datetime(2026, 7, 16, 8, 45),
    }
]

def seed_fake_emails(): 
    for fake_email in emails:
        # db.session.execute() executes
        # a query
        existing_email = db.session.execute(
            db.select(Email).filter_by(
                gmail_thread_id=fake_email["gmail_thread_id"]
            )
        # returns an Email object if it 
        # exists, else returns None
        ).scalar_one_or_none()

        if existing_email is None:
            # ** sets the values of the dict
            # to be values of the args of Email()
            email = Email(**fake_email)
            # queue the email to be 
            # inserted
            db.session.add(email)
    db.session.commit()

# create db table
with app.app_context() :
    # create missing tables
    db.create_all()
    # inserts any missing emails
    seed_fake_emails()

# homepage route
@app.route("/")
def dashboard() :
    emails = db.session.execute(
        db.select(Email).order_by(Email.priority.desc())
    ).scalars().all()
    # pass emails to template
    return render_template('dashboard.html', emails=emails)

# mark done route
@app.route("/emails/<int:email_id>/done", methods=["POST"])
def mark_done(email_id) :
    # if the email exists return Email object,
    # else return 404 Not Found page
    email = db.get_or_404(Email, email_id)

    email.status = "Done"
    db.session.commit()

    return redirect(url_for("dashboard"))

# mark waiting route
@app.route("/emails/<int:email_id>/waiting", methods=["POST"])
def mark_waiting(email_id) :
    email = db.get_or_404(Email, email_id)

    email.status = "Waiting"
    db.session.commit()

    return redirect(url_for("dashboard"))

# mark ignore route
@app.route("/emails/<int:email_id>/ignore", methods=["POST"])
def mark_ignore(email_id) :
    email = db.get_or_404(Email, email_id)

    email.status = "No Action"
    db.session.commit()

    return redirect(url_for("dashboard"))

if __name__ == "__main__" :
    app.run(debug=True)
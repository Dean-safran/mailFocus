from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

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

# create db table
with app.app_context() :
    db.create_all()

emails = [
    {
        "id": 1,
        "sender": "Professor Smith",
        "subject": "Please send your project",
        "priority": 90,
        "status": "Needs Reply"
    },
    {
        "id": 2,
        "sender": "GitHub",
        "subject": "New login detected",
        "priority": 60,
        "status": "Review"
    },
    {
        "id": 3,
        "sender": "Clothing Store",
        "subject": "20% off today",
        "priority": 10,
        "status": "No Action"
    },
    {
        "id": 4,
        "sender": "Polo Ralph",
        "subject": "New sweaters for sale",
        "priority": 10,
        "status": "No Action"
    }
]

# homepage route
@app.route("/")
def dashboard() :
    # sort emails
    emails.sort(key=lambda x: x["priority"], reverse=True)
    sorted_emails = emails
    # pass emails to template
    return render_template('dashboard.html', emails=sorted_emails)

# mark done route
@app.route("/emails/<int:email_id>/done", methods=["POST"])
def mark_done(email_id) :
    for email in emails :
        if email["id"] == email_id :
            email["status"] = "Done"
            break
    return redirect(url_for("dashboard"))

# mark waiting route
@app.route("/emails/<int:email_id>/waiting", methods=["POST"])
def mark_waiting(email_id) :
    for email in emails :
        if email["id"] == email_id :
            email["status"] = "Waiting"
            break
    return redirect(url_for("dashboard"))

# mark ignore route
@app.route("/emails/<int:email_id>/ignore", methods=["POST"])
def mark_ignore(email_id) :
    for email in emails :
        if email["id"] == email_id :
            email["status"] = "No Action"
            break
    return redirect(url_for("dashboard"))

if __name__ == "__main__" :
    app.run(debug=True)
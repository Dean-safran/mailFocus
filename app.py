from flask import (
    Flask, 
    render_template, 
    redirect, 
    url_for,
    request,
    session
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from services.classifier import classify_email

# imports for connecting gmail ->
from google_auth_oauthlib.flow import Flow
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

REDIRECT_URI = "http://127.0.0.1:5000/oauth/callback"


# configurations
# --------------
load_dotenv()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mailfocus.db"
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

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

    is_unread = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
        "subject": "Project results",
        "snippet": "Could you send me your results before Friday?",
        "is_unread": True,
        "gmail_thread_id": "fake-thread-1",
        "received_at": datetime(2026, 7, 15, 9, 30),
    },
    {
        "sender": "Career Center",
        "subject": "Internship application deadline",
        "snippet": "Please submit your application by Monday.",
        "is_unread": True,
        "gmail_thread_id": "fake-thread-2",
        "received_at": datetime(2026, 7, 16, 8, 45),
    },
    {
        "sender": "teammate@example.com",
        "subject": "Project update",
        "snippet": "Can you review this when you have time?",
        "is_unread": False,
        "gmail_thread_id": "fake-thread-3",
        "received_at": datetime(2026, 7, 16, 10, 15),
    },
    {
        "sender": "newsletter@example.com",
        "subject": "Weekly newsletter",
        "snippet": "Read this week's news. Unsubscribe here.",
        "is_unread": True,
        "gmail_thread_id": "fake-thread-4",
        "received_at": datetime(2026, 7, 14, 12, 0),
    },
    {
        "sender": "noreply@store.com",
        "subject": "20% off today",
        "snippet": "Limited-time sale. Shop now.",
        "is_unread": False,
        "gmail_thread_id": "fake-thread-5",
        "received_at": datetime(2026, 7, 13, 11, 0),
    },
    {
        "sender": "orders@store.com",
        "subject": "Order confirmation",
        "snippet": "Your order has been received.",
        "is_unread": True,
        "gmail_thread_id": "fake-thread-6",
        "received_at": datetime(2026, 7, 12, 16, 30),
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
            # run classifier and add 
            # attributes to email object
            classification = classify_email(fake_email)
            fake_email["priority"] = classification["priority"]
            fake_email["status"] = classification["status"]
            fake_email["reason"] = classification["reasons"]
            # ** sets the values of the fake_email dict
            # to be values of the args of Email()
            email = Email(**fake_email)
            # queue the email to be 
            # inserted
            db.session.add(email)
    db.session.commit()

# create service to access gmail API
def get_gmail_service() :
    # loads access and refresh tokens
    credentials = Credentials.from_authorized_user_file(
        "token.json",
        SCOPES,
    )

    # builds authenticated gmail API client
    service = build(
        "gmail",
        "v1",
        credentials=credentials,
    )

    return service

def get_message_header(headers, header_name, default_value=""):
    for header in headers:
        if header.get("name", "").lower() == header_name.lower():
            return header.get("value", default_value)

    return default_value

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

    gmail_connected = os.path.exists("token.json")

    # pass emails to template
    return render_template('dashboard.html', 
                           emails=emails,
                           gmail_connected=gmail_connected)

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


# CONNECTING GMAIL CODE 
# =======================================================
# connect gmail route
@app.route("/connect-gmail")
def connect_gmail() :
    # loads application identity
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        autogenerate_code_verifier=True,
    )

    # after user clicks Allow, send them back here
    flow.redirect_uri = REDIRECT_URI

    # builds the google permission page URL
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    session["oauth_state"] = state
    session["oauth_code_verifier"] = flow.code_verifier

    # sends browser to google
    return redirect(authorization_url)

@app.route("/oauth/callback")
def oauth_callback():
    # if an error variable was sent with url
    if request.args.get("error"):
        return "Google authorization was cancelled for denied.", 400
    
    # make sure callback belongs to login MailFocus started
    expected_state = session.pop("oauth_state", None)
    returned_state = request.args.get("state")
    # make sure MailFocus is the same app that started 
    # authorization request
    code_verifier = session.pop("oauth_code_verifier", None)

    if expected_state is None or returned_state != expected_state:
        return "OAuth state did not match. Please connect Gmail again.", 400
    
    if code_verifier is None :
        return "OAuth code verifier is missing.", 400
    
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        state=expected_state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )

    flow.redirect_uri = REDIRECT_URI

    # exchange authorization code for tokens
    # using google token endpoint (API)
    flow.fetch_token(
        authorization_response=request.url,
    )

    credentials = flow.credentials

    # save credentials
    with open("token.json", "w", encoding="utf-8") as token_file:
        token_file.write(credentials.to_json())

    return redirect(url_for("dashboard"))

@app.route("/gmail-preview")
def gmail_preview():
    if not os.path.exists("token.json"):
        return redirect(url_for("connect_gmail"))

    service = get_gmail_service()

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=10,
            q="in:inbox",
        )
        .execute()
    )

    message_references = response.get("messages", [])

    gmail_messages = []

    for message_reference in message_references:
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_reference["id"],
                format="metadata",
                metadataHeaders=[
                    "Subject",
                    "From",
                    "Date",
                ],
            )
            .execute()
        )

        headers = message.get("payload", {}).get("headers", [])

        gmail_message = {
            "id": message["id"],
            "thread_id": message.get("threadId", ""),
            "subject": get_message_header(
                headers,
                "Subject",
                "(No subject)",
            ),
            "sender": get_message_header(
                headers,
                "From",
                "(Unknown sender)",
            ),
            "date": get_message_header(
                headers,
                "Date",
                "(Unknown date)",
            ),
            "snippet": message.get("snippet", ""),
            "is_unread": "UNREAD" in message.get("labelIds", []),
        }

        gmail_messages.append(gmail_message)

    return render_template(
        "gmail_preview.html",
        gmail_messages=gmail_messages,
    )

# =======================================================

if __name__ == "__main__" :
    app.run(debug=True)
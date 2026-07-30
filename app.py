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

import base64

from services.gmail_parser import (
    get_message_header,
    normalize_gmail_message,
)

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

    gmail_message_id = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
    )

    gmail_thread_id = db.Column(
        db.String(255),
        nullable=False,
    )

    sender = db.Column(
        db.String(255),
        nullable=False
    )

    recipients = db.Column(
        db.Text,
        nullable=False,
        default="",
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

    body = db.Column(
        db.Text,
        nullable=False,
        default="",
    )

    is_unread = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
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
    
    received_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # lets us call email.gmail_url rather than email.gmail_url()
    @property
    def gmail_url(self):
        return (
            "https://mail.google.com/mail/"
            f"#all/{self.gmail_thread_id}"
        )




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

def decode_body_data(encoded_data):
    if not encoded_data:
        return ""

    padding = "=" * (-len(encoded_data) % 4)
    padded_data = encoded_data + padding

    decoded_bytes = base64.urlsafe_b64decode(padded_data)

    return decoded_bytes.decode(
        "utf-8",
        errors="replace",
    )

# create db table
with app.app_context() :
    # create missing tables
    db.create_all()



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

@app.route("/sync-gmail", methods=["POST"])
def sync_gmail():
    if not os.path.exists("token.json"):
        return redirect(url_for("connect_gmail"))

    service = get_gmail_service()

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=100,
            q="in:inbox",
        )
        .execute()
    )

    message_references = response.get("messages", [])

    imported_count = 0
    skipped_count = 0

    for message_reference in message_references:
        gmail_message_id = message_reference["id"]

        existing_email = db.session.execute(
            db.select(Email).filter_by(
                gmail_message_id=gmail_message_id,
            )
        ).scalar_one_or_none()

        if existing_email is not None:
            skipped_count += 1
            continue

        gmail_message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=gmail_message_id,
                format="full",
            )
            .execute()
        )

        normalized_email = normalize_gmail_message(
            gmail_message
        )

        classification = classify_email(
            normalized_email
        )

        email = Email(
            gmail_message_id=normalized_email[
                "gmail_message_id"
            ],
            gmail_thread_id=normalized_email[
                "gmail_thread_id"
            ],
            sender=normalized_email["sender"],
            recipients=", ".join(
                normalized_email["recipients"]
            ),
            subject=normalized_email["subject"],
            snippet=normalized_email["snippet"],
            body=normalized_email["body"],
            is_unread=normalized_email["is_unread"],
            received_at=normalized_email["received_at"],
            priority=classification["priority"],
            status=classification["status"],
            reason=classification["reasons"],
        )

        db.session.add(email)
        imported_count += 1

    db.session.commit()

    print(
        f"Gmail sync complete: "
        f"{imported_count} imported, "
        f"{skipped_count} skipped."
    )

    return redirect(url_for("dashboard"))

# =======================================================

if __name__ == "__main__" :
    app.run(debug=True)
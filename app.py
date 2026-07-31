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
from googleapiclient.errors import HttpError

import base64

from services.gmail_parser import (
    get_message_header,
    normalize_gmail_message,
    normalize_gmail_thread,
)
from services.thread_analyzer import analyze_thread




# Global variables
# ----------------
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
        nullable=False,
    )

    gmail_thread_id = db.Column(
        db.String(255),
        unique=True,
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




# Functions
# ---------

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


def get_current_user_email(service):
    profile = (
        service.users()
        .getProfile(userId="me")
        .execute()
    )

    return profile["emailAddress"].lower()


def remove_threads_no_longer_in_inbox(service):
    saved_threads = db.session.execute(
        db.select(Email)
    ).scalars().all()

    removed_count = 0

    for saved_thread in saved_threads:
        try:
            gmail_thread = (
                service.users()
                .threads()
                .get(
                    userId="me",
                    id=saved_thread.gmail_thread_id,
                    format="minimal",
                )
                .execute()
            )

        except HttpError as error:
            if error.resp.status == 404:
                db.session.delete(saved_thread)
                removed_count += 1
                continue

            raise

        messages = gmail_thread.get("messages", [])

        thread_is_in_inbox = any(
            "INBOX" in message.get("labelIds", [])
            for message in messages
        )

        if not thread_is_in_inbox:
            db.session.delete(saved_thread)
            removed_count += 1

    return removed_count



# create db table
# ----------------
with app.app_context() :
    # create missing tables
    db.create_all()




# Routes
# -------

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


# CONNECTING GMAIL ROUTES 
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
    user_email = get_current_user_email(service)

    removed_count = remove_threads_no_longer_in_inbox(service)

    response = (
        service.users()
        .threads()
        .list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=30,
        )
        .execute()
    )

    thread_references = response.get("threads", [])

    imported_count = 0
    updated_count = 0
    unchanged_count = 0

    for thread_reference in thread_references:
        gmail_thread_id = thread_reference["id"]

        # fetch every message in one thread
        gmail_thread = (
            service.users()
            .threads()
            .get(
                userId="me",
                id=gmail_thread_id,
                format="full",
            )
            .execute()
        )

        # normalize thread object into a dictionary
        # and sort
        normalized_thread = normalize_gmail_thread(
            gmail_thread
        )
        messages = normalized_thread["messages"]

        if not messages:
            continue

        # analyze who owes next action
        analysis = analyze_thread(
            normalized_thread,
            user_email,
        )

        newest_message = analysis["newest_message"]

        # check if thread already exists in database
        existing_thread = db.session.execute(
            db.select(Email).filter_by(
                gmail_thread_id=gmail_thread_id,
            )
        ).scalar_one_or_none()

        # if thread object is not in database
        if existing_thread is None:
            email = Email(
                gmail_message_id=newest_message[
                    "gmail_message_id"
                ],
                gmail_thread_id=gmail_thread_id,
                sender=newest_message["sender"],
                recipients=", ".join(
                    newest_message["recipients"]
                ),
                subject=newest_message["subject"],
                snippet=newest_message["snippet"],
                body=newest_message["body"],
                is_unread=newest_message["is_unread"],
                received_at=newest_message["received_at"],
                priority=analysis["priority"],
                status=analysis["status"],
                reason=analysis["reasons"],
            )

            db.session.add(email)
            imported_count += 1
            continue

        # check if thread needs to be updated
        thread_has_new_message = (
            existing_thread.gmail_message_id
            != newest_message["gmail_message_id"]
        )

        # if thread doesn't need to be updated
        if not thread_has_new_message:
            unchanged_count += 1
            continue

        # update thread with most recent message
        existing_thread.gmail_message_id = (
            newest_message["gmail_message_id"]
        )
        existing_thread.sender = newest_message["sender"]
        existing_thread.recipients = ", ".join(
            newest_message["recipients"]
        )
        existing_thread.subject = newest_message["subject"]
        existing_thread.snippet = newest_message["snippet"]
        existing_thread.body = newest_message["body"]
        existing_thread.is_unread = newest_message["is_unread"]
        existing_thread.received_at = newest_message[
            "received_at"
        ]
        existing_thread.priority = analysis["priority"]
        existing_thread.status = analysis["status"]
        existing_thread.reason = analysis["reasons"]

        updated_count += 1

    db.session.commit()

    print(
        "Gmail sync complete: "
        f"{imported_count} threads imported, "
        f"{updated_count} threads updated, "
        f"{unchanged_count} threads unchanged, "
        f"{removed_count} threads removed."
    )

    return redirect(url_for("dashboard"))


@app.route("/test-thread")
def test_thread():
    if not os.path.exists("token.json"):
        return redirect(url_for("connect_gmail"))

    service = get_gmail_service()
    user_email = get_current_user_email(service)

    response = (
        service.users()
        .threads()
        .list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=30,
        )
        .execute()
    )

    thread_references = response.get("threads", [])
    selected_thread = None

    for thread_reference in thread_references:
        gmail_thread = (
            service.users()
            .threads()
            .get(
                userId="me",
                id=thread_reference["id"],
                format="full",
            )
            .execute()
        )

        messages = gmail_thread.get("messages", [])

        if len(messages) >= 2:
            selected_thread = gmail_thread
            break

    if selected_thread is None:
        return (
            "No recent inbox thread with multiple "
            "messages was found."
        )

    normalized_thread = normalize_gmail_thread(
        selected_thread
    )

    analysis = analyze_thread(
        normalized_thread,
        user_email,
    )

    messages = normalized_thread["messages"]
    newest_message = analysis["newest_message"]

    print("\n--- THREAD ACTION ANALYSIS ---")
    print("Number of messages:", len(messages))

    for index, message in enumerate(
        messages,
        start=1,
    ):
        print(f"\nMessage {index}")
        print("Sender:", message["sender"])
        print("Received at:", message["received_at"])
        print("Body preview:", message["body"][:150])

    print("\nNewest message:")
    print("Sender:", newest_message["sender"])
    print(
        "Sent by current user:",
        analysis["newest_sent_by_user"],
    )

    print("\nThread result:")
    print("Status:", analysis["status"])
    print("Priority:", analysis["priority"])
    print("Reason:", analysis["reasons"])
    print("--------------------------------\n")

    return (
        f"Thread analyzed as {analysis['status']}. "
        f"Check the Flask terminal."
    )

# =======================================================

if __name__ == "__main__" :
    app.run(debug=True)
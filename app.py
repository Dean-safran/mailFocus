from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

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
            email["status"] = "Ignored"
            break
    return redirect(url_for("dashboard"))

if __name__ == "__main__" :
    app.run(debug=True)
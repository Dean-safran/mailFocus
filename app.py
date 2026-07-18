from flask import Flask, render_template

app = Flask(__name__)

emails = [
    {
        "sender": "Professor Smith",
        "subject": "Please send your project",
        "priority": 90,
        "status": "Needs Reply"
    },
    {
        "sender": "GitHub",
        "subject": "New login detected",
        "priority": 60,
        "status": "Review"
    },
    {
        "sender": "Clothing Store",
        "subject": "20% off today",
        "priority": 10,
        "status": "No Action"
    },
    {
        "sender": "Polo Ralph",
        "subject": "New sweaters for sale",
        "priority": 10,
        "status": "No Action"
    }
]

@app.route("/")
def dashboard() :
    emails.sort(key=lambda x: x["priority"], reverse=True)
    sorted_emails = emails
    return render_template('dashboard.html', emails=sorted_emails)

if __name__ == "__main__" :
    app.run(debug=True)
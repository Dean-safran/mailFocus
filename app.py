from flask import Flask

app = Flask(__name__)

@app.route("/")
def home() :
    return "<h1>Hello, MailFocus!</h1><p>My first web app</p>"

if __name__ == "__main__" :
    app.run(debug=True)
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/login")
def hello_world():
    return render_template("login.html")

@app.route("/register")
def hello_world():
    return render_template("register.html")

@app.route("/what")
def hello_world():
    return render_template("what.html")

@app.route("/contact")
def hello_world():
    return render_template("contact.html")
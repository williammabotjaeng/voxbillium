from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/what")
def what():
    return render_template("what.html")

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")
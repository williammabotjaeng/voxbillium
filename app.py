from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from flask_mail import Message, Mail
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import InputRequired, Length, DataRequired, Email
from dotenv import load_dotenv
from datetime import datetime

# from google.cloud import api_keys_v2
# from google.cloud.api_keys_v2 import Key
from google.cloud import api_keys_v2
from google.cloud.api_keys_v2 import Key

import argparse

from google.cloud import speech

import moment
import requests
import os



app = Flask(__name__)

load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'QPEunVzlmptwr73MfPz44w=='
api_token = os.getenv("API_TOKEN")
log_config_id = os.getenv("CONFIG_ID")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")  # Replace with your email address
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD") # Replace with your email password
app.config["PROJECT_ID"] = os.getenv("PROJECT_ID") 

mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=True)
    first_name = db.Column(db.String(20), nullable=True)
    last_name = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15))
    address = db.Column(db.String(200))

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15))
    address = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    invoices = db.relationship('Invoice', backref='customer', lazy=True)
    payment_methods = db.relationship('PaymentMethod', backref='customer', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='customer', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    sku_code = db.Column(db.String(50))

    # Add any other fields relevant to the product model
    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    invoice_number = db.Column(db.String(20), nullable=False)
    invoice_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.String(200))
    billing_address = db.Column(db.String(200))
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)

    items = db.relationship('InvoiceItem', backref='invoice', lazy=True)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    payment_method = db.relationship('PaymentMethod', backref='payments')
    invoice = db.relationship('Invoice', backref='payments')
    user = db.relationship('User', backref='payments')

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_api_key(project_id: str, suffix: str) -> Key:
    # Create the API Keys client.
    client = api_keys_v2.ApiKeysClient()

    key = api_keys_v2.Key()
    key.display_name = f"My first API key - {suffix}"

    # Initialize request and set arguments.
    request = api_keys_v2.CreateKeyRequest()
    request.parent = f"projects/{project_id}/locations/global"
    request.key = key

    # Make the request and wait for the operation to complete.
    response = client.create_key(request=request).result()

    print(f"Successfully created an API key: {response.name}")
    # For authenticating with the API key, use the value in "response.key_string".
    # To restrict the usage of this API key, use the value in "response.name".
    return response


# [START speech_transcribe_streaming]
def transcribe_streaming(stream_file: str) -> speech.RecognitionConfig:
    """Streams transcription of the given audio file."""

    client = speech.SpeechClient()

    # [START speech_python_migration_streaming_request]
    with open(stream_file, "rb") as audio_file:
        content = audio_file.read()

    # In practice, stream should be a generator yielding chunks of audio data.
    stream = [content]

    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config)

    # streaming_recognize returns a generator.
    # [START speech_python_migration_streaming_response]
    responses = client.streaming_recognize(
        config=streaming_config,
        requests=requests,
    )
    # [END speech_python_migration_streaming_request]

    for response in responses:
        # Once the transcription has settled, the first result will contain the
        # is_final result. The other results will be for subsequent portions of
        # the audio.
        for result in response.results:
            print(f"Finished: {result.is_final}")
            print(f"Stability: {result.stability}")
            alternatives = result.alternatives
            # The alternatives are ordered from most likely to least.
            for alternative in alternatives:
                print(f"Confidence: {alternative.confidence}")
                print(f"Transcript: {alternative.transcript}")

    # [END speech_python_migration_streaming_response]


# [END speech_transcribe_streaming]


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=64)])

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=64)])

class CustomerForm(FlaskForm):
    first_name = StringField('First Name', validators=[InputRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[InputRequired(), Length(min=6, max=100)])
    phone_number = StringField('Phone Number')
    address = StringField('Address')
    user_id = StringField('User ID', validators=[InputRequired()])
    submit = SubmitField('Create Customer')

class ContactUsForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    return render_template("index.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('login'))

            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
   
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            user = User.query.filter_by(email=email).first()
            if user:
                flash('Username already exists. Please choose a different one.')
                return redirect(url_for('login'))

            new_user = User(email=email, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            message_body = """We are thrilled to welcome you to VoxBillium, the revolutionary web app that is set to transform the way you generate invoices. With VoxBillium, you can harness the power of voice commands to streamline your billing process and save valuable time and effort.\nInspired by the capabilities of AI, VoxBillium seamlessly combines ancient wisdom with cutting-edge technology to simplify your invoicing tasks. Our app empowers you to effortlessly create and manage invoices using your voice, allowing you to multitask and focus on what truly matters in your everyday life.
            \nFrom freelancers to small businesses, VoxBillium is designed to cater to your invoicing needs. Whether you\'re on the go or tied up with other responsibilities, VoxBillium lets you stay on top of your billing tasks with ease, all at the convenience of a few simple voice commands.
            \nWe invite you to embrace the efficiency and convenience of VoxBillium today. Experience a new level of productivity as you navigate the world of invoice generation with ease and simplicity.
            \nTo get started, simply visit our website and follow the quick and easy registration process. Once you're in, you'll have access to a range of powerful features and tools designed to enhance your invoicing experience.
            \nIf you have any questions or need assistance, our dedicated support team is here to help. Don't hesitate to reach out to us at voxbillium@gmail.com.
            \nThank you for choosing VoxBillium as your go-to invoicing companion. We're excited to have you on board and can't wait to witness the positive impact VoxBillium will have on your invoicing workflow.
            \nWishing you success and efficiency in all your invoicing endeavors!
            \nBest regards,
            \n\nVoxBillium Team"""
          
            # Send email to the new user
            msg = Message(
                subject="Welcome to VoxBillium - Simplify Invoice Generation with Voice Commands!",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email],
                body=f"Hi {email},\n\n{message_body}"
            )
            mail.send(msg)

            flash('Registration successful! An email has been sent to your email address.')
            user = User.query.filter_by(email=email).first()
            login_user(user)
            print("User Created")
            return redirect(url_for('home'))
    return render_template("register.html", form=form)

@login_required
@app.route("/home")
def home():
    form = CustomerForm()
    api_key_res = create_api_key(app.config["PROJECT_ID"], "billium")
    print("API KEY Response", api_key_res)
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", current_user=current_user, form=form, customers=customers)

@login_required
@app.route("/check/<int:contact_id>", methods=["POST"])
def check(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    # Perform verification process using the ip_address field
    vpn_data = {
        "ip": contact.ip_address,
        "provider": "digitalelement"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    vpn_response = requests.post("https://ip-intel.aws.eu.pangea.cloud/v1/vpn", json=vpn_data, headers=headers)

    proxy_data = {
        "ip": contact.ip_address,
        "provider": "digitalelement"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    proxy_response = requests.post("https://ip-intel.aws.eu.pangea.cloud/v1/proxy", json=proxy_data, headers=headers)

    sanctions_data = {
        "ip": contact.ip_address
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    sanctions_response = requests.post("https://embargo.aws.eu.pangea.cloud/v1/ip/check", json=sanctions_data, headers=headers)

    breached_data = {
        "email": contact.email,
        "provider": "spycloud"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    breached_response = requests.post("https://user-intel.aws.eu.pangea.cloud/v1/user/breached", json=breached_data, headers=headers)

    
    # Handle the response as needed
    if sanctions_response.status_code == 200 and vpn_response.status_code == 200 and proxy_response.status_code == 200 and breached_response.status_code == 200:
        contact.sanction_status = "Yes" if sanctions_response.json()['result']['count'] > 0 else "No"
        contact.vpn_status = "Yes" if vpn_response.json()['result']['data']['is_vpn'] else "No"
        contact.proxy_status = "Yes" if proxy_response.json()['result']['data']['is_proxy'] else "No"
        contact.breached_status = "Yes" if breached_response.json()['result']['data']['found_in_breach'] else "No"

        # Log the contact deletion event
        log_data = {
            "config_id": f"{log_config_id}",
            'event': {
                'message': 'Checking Contact Compliance'
            }
        }

        headers = {
            'Authorization': f"Bearer {api_token}",
            'Content-Type': 'application/json'
        }

        response = requests.post('https://audit.aws.eu.pangea.cloud/v1/log', json=log_data, headers=headers)
        res = response.json()

        # Save the log data to the database
        log = Log(
            message=log_data['event']['message'],
            actor=current_user.id,
            action='check compliance',
            target='Contact',
            status='success',
            request_time=res['request_time']
        )

        db.session.add(log)
  

        db.session.commit()

    return redirect(url_for("compliance"))

@app.route("/create_invoice", methods=["GET", "POST"])
@login_required
def create_invoice():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        invoice_number = request.form.get("invoice_number")
        invoice_date = request.form.get("invoice_date")
        total_amount = request.form.get("total_amount")
        status = request.form.get("status")
        shipping_address = request.form.get("shipping_address")
        billing_address = request.form.get("billing_address")
        payment_method_id = request.form.get("payment_method_id")

        new_invoice = Invoice(
            customer_id=customer_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            total_amount=total_amount,
            status='Pending',
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment_method_id=payment_method_id
        )

        db.session.add(new_invoice)
        db.session.commit()

        print(Invoice.query.filter_by(customer_id=customer_id).all())

        return redirect(url_for("invoices"))
    
    return render_template("create_invoice.html", current_user=current_user)

@app.route("/start_invoice", methods=["GET", "POST"])
def start_invoice():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("stream", help="File to stream to the API")
    args = parser.parse_args()
    print("Arguments Passed", args)
    res = transcribe_streaming(args.stream)
    print(res)
    return render_template("create_invoice.html")

@app.route("/what")
def what():
    return render_template("what.html")

@app.route("/getintouch", methods=["GET", "POST"])
def contact():
    form = ContactUsForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data

        msg = Message(
            subject="New Message from Contact Form",
            sender=app.config["MAIL_USERNAME"],
            recipients=["VoxBilliumapp@gmail.com"],
            body=f"Name: {name}\nEmail: {email}\nMessage: {message}"
        )

        mail.send(msg)

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("home"))

    return render_template("getintouch.html", form=form, current_user=current_user)

@app.route("/customers")
@login_required
def customers():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template("customers.html", current_user=current_user, customers=customers)

@app.route("/invoices")
@login_required
def invoices():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    invoices = []
    for customer in customers:
        invoices.extend(customer.invoices)
    return render_template("invoices.html", current_user=current_user, invoices=invoices)

@app.route("/create_customer", methods=["GET", "POST"])
@login_required
def create_customer():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        address = request.form.get("address")

        new_customer = Customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            address=address,
            user_id=current_user.id  
        )

        db.session.add(new_customer)
        db.session.commit()

        print(Customer.query.filter_by(user_id=current_user.id).all())

        return redirect(url_for("customers"))
    
    return render_template("create_customer.html", current_user=current_user)


@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
@login_required
def delete_customer(customer_id):

    customer = Customer.query.filter_by(user_id=current_user.id, id=customer_id).first()

    if customer:
        db.session.delete(customer)
        db.session.commit()

    db.session.commit()

    return redirect(url_for("customers"))

@app.route("/customers/edit/<int:customer_id>", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.filter_by(user_id=current_user.id, id=customer_id).first()
    if not customer:
        return redirect(url_for("customers"))

    if request.method == "POST":
        # Update the customer object with the new data from the form
        print(request.form)
        customer.first_name = request.form.get("first_name")
        customer.last_name = request.form.get("last_name")
        customer.email = request.form.get("email")
        customer.phone_number = request.form.get("phone_number")
        customer.address = request.form.get("address")

        db.session.commit()


        return redirect(url_for("customers"))
    else:
        return render_template("edit_customer.html", current_user=current_user, customer=customer)
    
@app.route("/assign/<int:customer_id>", methods=["GET"])
@login_required
def verify_contact(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template("create_invoice.html", customer=customer)

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

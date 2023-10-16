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
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", current_user=current_user, form=form, customers=customers)

@login_required
@app.route("/compliance", methods=["GET"])
def compliance():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template("compliance.html", current_user=current_user, contacts=contacts)

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

@app.route("/contacts")
@login_required
def contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template("contacts.html", current_user=current_user, contacts=contacts)

import requests

@app.route("/create_contact", methods=["GET", "POST"])
@login_required
def create_contact():
    print("Config ID", log_config_id)
    print("API Token", api_token)
    if request.method == "POST":
        contact_type = request.form.get("contact_type")
        first_name = request.form.get("first_name")
        email = request.form.get("email")
        ip_address = request.form.get("ip_address")

        new_contact = Contact(
            contact_type=contact_type,
            first_name=first_name,
            email=email,
            ip_address=ip_address,
            user_id=current_user.id  
        )

        db.session.add(new_contact)
        db.session.commit()
        
        # Log the contact creation event
        log_data = {
            "config_id": f"{log_config_id}",
            'event': {
                'message': 'Creating Contact'
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
            action='create',
            target='Contact',
            status='success',
            request_time=res['request_time']
        )
        db.session.add(log)
        db.session.commit()

        return redirect(url_for("contacts"))
    
    return render_template("create_contact.html", current_user=current_user)

@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
@login_required
def delete_contact(contact_id):
    app.logger.info('Deleting contact with ID: %s', contact_id)

    contact = Contact.query.filter_by(user_id=current_user.id, id=contact_id).first()
    if contact:
        app.logger.info('Contact found. Deleting contact: %s', contact)
        db.session.delete(contact)
        db.session.commit()
    else:
        app.logger.warning('Contact not found with ID: %s', contact_id)

    # Log the contact deletion event
    log_data = {
        "config_id": f"{log_config_id}",
        'event': {
            'message': 'Deleting contact'
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
        action='delete',
        target='Contact',
        status='success',
        request_time=res['request_time']
    )
    db.session.add(log)
    db.session.commit()

    app.logger.info('Contact deletion completed')
    return redirect(url_for("contacts"))

@app.route("/contacts/edit/<int:contact_id>", methods=["GET", "POST"])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.filter_by(user_id=current_user.id, id=contact_id).first()
    print("Contact: ", contact)
    if not contact:
        return redirect(url_for("contacts"))

    if request.method == "POST":
        # Update the contact object with the new data from the form
        print(request.form)
        contact.first_name = request.form.get("first_name")
        contact.last_name = request.form.get("last_name")
        contact.email = request.form.get("email")
        contact.phone_number = request.form.get("phone_number")
        contact.address = request.form.get("address")
        contact.status = request.form.get("status")
        contact.ip_address = request.form.get("ip_address")
        db.session.commit()

        # Log the contact update event
        log_data = {
            "config_id": f"{log_config_id}",
            'event': {
                'message': 'Updating Contact'
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
            action='update',
            target='Contact',
            status='success',
            request_time=res['request_time']
        )
        db.session.add(log)
        db.session.commit()

        print("Done, Saved Data!")
        return redirect(url_for("contacts"))
    else:
        return render_template("edit_contact.html", current_user=current_user, contact=contact)


@app.route("/verify/<int:contact_id>", methods=["POST"])
@login_required
def verify_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)

    # Perform verification process using the ip_address field
    verification_data = {
        "ip": contact.ip_address,
        "provider": "cymru"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://ip-intel.aws.eu.pangea.cloud/v1/reputation", json=verification_data, headers=headers)

    # Handle the response as needed
    if response.status_code == 200:
        verification_result = response.json()
        verdict = verification_result.get("result", {}).get("data", {}).get("verdict")
        if verdict == "benign":
            contact.status = "Trusted"
        else:
            contact.status = "Untrusted"

        # Log the contact deletion event
        log_data = {
            "config_id": f"{log_config_id}",
            'event': {
                'message': 'Verifying contact'
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
            action='verify',
            target='Contact',
            status='success',
            request_time=res['request_time']
        )

        db.session.add(log)
  

        db.session.commit()

    return redirect(url_for("contacts"))

@app.route("/logs")
@login_required
def logs():
    user_id = current_user.id

    # Retrieve logs from the database with the current_user's id as the actor field
    logs = Log.query.filter_by(actor=user_id).all()
    for log in logs:
        print(log.request_time)

    return render_template("logs.html", logs=logs, moment=moment, datetime=datetime)

@app.route("/get_contact", methods=["GET", "POST"])
@login_required
def get_contact():
    if request.method == "POST":
        email = request.form.get("email")
        contact = Contact.query.filter_by(email=email).first()

        if contact:
            # Contact found, do something with it
            return render_template("contact_details.html", contact=contact)
        else:
            # Contact not found
            return render_template("contact_not_found.html")
    
    return render_template("get_contact.html", current_user=current_user)

@app.route("/trusted_contacts", methods=["GET"])
@login_required
def get_trusted_contacts():
    trusted_contacts = Contact.query.filter_by(status="Trusted").all()

    return render_template("trusted_contacts.html", contacts=trusted_contacts)

@app.route("/untrusted_contacts", methods=["GET"])
@login_required
def get_untrusted_contacts():
    untrusted_contacts = Contact.query.filter_by(status="Untrusted").all()

    return render_template("untrusted_contacts.html", contacts=untrusted_contacts)

@app.route("/latest_contact", methods=["GET"])
@login_required
def get_latest_contact():
    latest_contact = Contact.query.order_by(Contact.created_at.desc()).first()

    return render_template("latest_contact.html", contact=latest_contact)

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

import os
import hashlib
import binascii
from flask import current_app, render_template
from flask_mail import Mail, Message
from functools import wraps
from flask import redirect, url_for
from flask_login import current_user
from dotenv import load_dotenv
import cloudinary.uploader
from cryptography.fernet import Fernet


load_dotenv(".env")

# Initialise the Fernet cipher suite
cipher_suite = Fernet(os.getenv("FERNET_KEY").encode())


# Function to encrypt the order_id
def encrypt_order_id(order_id):
    return cipher_suite.encrypt(str(order_id).encode()).decode()


# Function to decrypt the encrypted order_id
def decrypt_order_id(encrypted_order_id):
    return int(cipher_suite.decrypt(encrypted_order_id.encode()).decode())


def get_image_url(image_name):
    cloudinary.config(
        cloud_name=os.getenv("CLOUD_NAME"),
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET"),
    )
    return cloudinary.uploader.upload(image_name)["url"]


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            # If the user is not authenticated, redirect to a different login endpoint
            return redirect(url_for("home_blueprint.login"))

        # If the user is not an admin, inform them the page doesn't exist
        if not current_user.is_admin:
            return render_template("home/admin-page-404.html"), 404
        return func(*args, **kwargs)

    return decorated_view


def user_logged_in(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            # If the user is not authenticated, redirect to a different login endpoint
            return redirect(url_for("home_blueprint.login"))
        return func(*args, **kwargs)

    return decorated_view


def password_callable(character: str) -> bool:
    return character.isdigit() or character.isupper() or (not character.isalnum())


def is_valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    return any(lambda a: password_callable(char) for char in password)


# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/
def hash_pass(password):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return salt + pwdhash  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""

    stored_password = stored_password.decode("ascii")
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac(
        "sha512", provided_password.encode("utf-8"), salt.encode("ascii"), 100000
    )
    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
    return pwdhash == stored_password


def send_enquiry_email_to_admin(company_email, company_name, name, email, message):
    mail = Mail(current_app)
    try:
        sender = "noreply@app.com"
        # Send a notification email to the admin
        admin_msg_title = "New Message Received"
        admin_msg = Message(admin_msg_title, sender=sender, recipients=[company_email])
        admin_msg_body = f"New message received from {name} ({email})."
        admin_msg.body = admin_msg_body
        admin_msg.reply_to = company_email
        admin_data = {
            "app_name": company_name,
            "title": admin_msg_title,
            "body": admin_msg_body,
            "name": name,
            "message": message,
        }
        admin_msg.html = render_template("emails/contact_admin.html", data=admin_data)

        # Send the notification email to the admin
        mail.send(admin_msg)
    except Exception as e:
        print(e)

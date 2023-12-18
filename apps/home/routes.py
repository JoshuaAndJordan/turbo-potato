import logging
from apps.home import blueprint
from flask import jsonify
from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from apps import db, login_manager
from apps.home.forms import LoginForm, CreateAccountForm, SearchForm
from apps.home.models import User
from apps.home.util import verify_pass
from apps.home.models import (
    Order,
    OrderItem,
)
from apps.home.util import (
    send_enquiry_email_to_admin,
    admin_required,
    is_valid_password,
    user_logged_in,
    encrypt_order_id,
    decrypt_order_id,
)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from dotenv import load_dotenv
import stripe
import os
from datetime import datetime

# Load environment variables from the .env file
load_dotenv()

# This is your test secret API key.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Access CSRFProtect directly
csrf = CSRFProtect()


@blueprint.route("/index")
@login_required
def index():
    form = SearchForm()
    return render_template("home/index.html", form=form)


@blueprint.route("/")
def route_default():
    return redirect(url_for("home_blueprint.price_monitoring_tasks_route"))


@blueprint.route("/support")
@login_required
def support_route():
    return redirect(url_for("home_blueprint.price_monitoring_tasks_route"))


@blueprint.route("/edit_profile")
@login_required
def edit_profile_route():
    return render_template("home/edit_profile.html", current_user=current_user)


@blueprint.route("/price_monitoring")
@login_required
def price_monitoring_tasks_route():
    return render_template("home/pricing.html")


@blueprint.route("/account_monitoring")
@login_required
def account_monitoring_tasks_route():
    return render_template("home/pricing.html")


# Login & Registration
@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if not login_form.validate_on_submit():
        return render_template("accounts/login.html", form=login_form)

    username = login_form.username.data
    password = login_form.password.data
    remember_me = login_form.remember_me.data

    # Query to check if the username already exists
    print(f"Username given is {username} and password is {password}")

    user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
    if not user:
        msg = "Invalid Username or Password."
        logging.info(msg)
        return render_template(
            "accounts/login.html", msg=msg, success=False, form=login_form
        )

    # check credentials
    if verify_pass(password, user.password):
        logging.info("Password Verified")
        # credentials are valid
        login_user(user, remember=remember_me)
        logging.info("Login successful")
        return redirect(url_for("home_blueprint.index"))
    else:
        # credentials are invalid
        msg = "Invalid Username or Password."
        logging.info(msg)
        # flash(msg)
        return render_template(
            "accounts/login.html", msg=msg, success=False, form=login_form
        )


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    create_account_form = CreateAccountForm(request.form)

    # Check if it's a post request
    if request.method == "POST":
        # Check if email and passwords match in their repeating fields
        if (
            create_account_form.password.data
            != create_account_form.confirm_password.data
        ):
            msg = "Passwords do not match"
            logging.info(msg)
            return render_template(
                "accounts/register.html",
                msg=msg,
                success=False,
                form=create_account_form,
            )
        if create_account_form.email.data != create_account_form.confirm_email.data:
            msg = "Email addresses do not match"
            logging.info(msg)
            return render_template(
                "accounts/register.html",
                msg=msg,
                success=False,
                form=create_account_form,
            )

        # Check if the password meets the given criteria
        if not is_valid_password(create_account_form.password.data):
            msg = (
                "Make sure the password is at least 6 characters long, contains at least one digit, one upper case"
                " and one special symbol"
            )
            logging.info(msg)
            # flash(msg)
            return render_template(
                "accounts/register.html",
                msg=msg,
                success=False,
                form=create_account_form,
            )

        logging.info("We are about to enter the register route")
        if create_account_form.validate_on_submit():
            logging.info("We have been sent a post message")
            if not create_account_form.term_agreement.data:
                msg = "You need to agree to the terms"
                flash(msg)
                logging.info(msg)
                return render_template(
                    "accounts/register.html",
                    msg=msg,
                    success=False,
                    form=create_account_form,
                )
            # Check username exists
            user = User.query.filter_by(
                username=create_account_form.username.data
            ).first()
            if user:
                msg = "Username already registered"
                logging.info(msg)
                flash(msg)
                return render_template(
                    "accounts/register.html",
                    msg=msg,
                    success=False,
                    form=create_account_form,
                )

            # Check email exists
            user = User.query.filter_by(email=create_account_form.email.data).first()
            if user:
                msg = "Email already registered"
                flash(msg)
                logging.info(msg)
                return render_template(
                    "accounts/register.html",
                    msg=msg,
                    success=False,
                    form=create_account_form,
                )

            # else we can create the user
            user = User(
                first_name=create_account_form.first_name.data,
                last_name=create_account_form.last_name.data,
                username=create_account_form.username.data,
                email=create_account_form.email.data,
                password=create_account_form.password.data,
            )

            db.session.add(user)
            db.session.commit()
            logging.info("Registration successful")

            return redirect(url_for('home_blueprint.login'))
        else:
            logging.info("Form not validated")
            logging.info(create_account_form.errors)
            return render_template("accounts/register.html", form=create_account_form)
    return render_template("accounts/register.html", form=create_account_form)


# Route to delete a user
@blueprint.route("/user/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 201


# Route to get all users
@blueprint.route("/all-user", methods=["GET"])
@admin_required
def get_users():
    try:
        logging.info("Fetching all users")
        users = User.query.all()
        return jsonify({"data": [user.format() for user in users], "total": len(users)})
    except Exception as e:
        logging.error(e)
        return jsonify({"message": str(e)}), 500


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home_blueprint.login"))


# Errors
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(_):
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(_):
    return render_template("home/page-404.html"), 404


@blueprint.errorhandler(500)
def internal_error(_):
    return render_template("home/page-500.html"), 500


# Helper - Extract current page name from request
def get_segment(req):
    try:
        segment = req.path.split("/")[-1]
        if segment == "":
            segment = "index"
        return segment
    except Exception as e:
        logging.info(e)
        return None


@blueprint.route("/contact", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form["Name"]
        email = request.form["Email"]
        message = request.form["Message..."]

        # Do something with the form data (e.g., store it, process it, etc.)
        # For example, you can print it to the console
        logging.info(f"Name: {name}, Email: {email}, Message: {message}")

        company_choice_record = CompanyChoice.query.first()
        company = None
        if company_choice_record:
            company_id_to_query = company_choice_record.company_choice
            company = Company.query.get(company_id_to_query)

        if not company:
            return jsonify({"message": "Company not found"}), 404

        company_email = company.email
        company_name = company.name

        # Flash a success message
        flash("Thanks for submitting!")

        send_enquiry_email_to_admin(company_email, company_name, name, email, message)

        # Render the HTML template (contact page) again
        return render_template("home/contact.html")

    # If it's a GET request or after form submission, render the HTML template
    return render_template("home/contact.html")


@blueprint.route("/get_csrf_token", methods=["GET"])
def get_csrf_token():
    csrf_token = current_app.jinja_env.globals["csrf_token"]()  # Generating CSRF token
    return jsonify({"csrf_token": csrf_token}), 200


# handle all templates
@blueprint.route("/<template_name>", methods=["GET"])
def templates(template_name):
    return render_template(f"home/{template_name}.html")


@blueprint.route("/admin-home", methods=["GET"])
@admin_required
def admin_home():
    return render_template("home/admin-home.html")


# Route to make a user admin
@blueprint.route("/admin/user/<int:user_id>/make_admin", methods=["POST"])
@admin_required
def make_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    user.is_admin = True
    db.session.commit()
    return jsonify({"message": "User is now admin"}), 200


# Route to remove admin privileges from a user
@blueprint.route("/admin/user/<int:user_id>/remove_admin", methods=["POST"])
@admin_required
def remove_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    user.is_admin = False
    db.session.commit()
    return jsonify({"message": "User is no longer admin"}), 200


# Route to create a checkout session on stripe
@blueprint.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        order_date = datetime.utcnow()
        total_price = data.get("total_price")
        cart_items = data.get("cart_items")
        # Create a new Order instance
        new_order = Order(
            user_id=user_id, order_date=order_date, total_price=total_price
        )
        db.session.add(new_order)
        db.session.commit()

        line_items = []
        for item in cart_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            product = Product.query.get(item["product_id"])
            price = (
                product.price
            )  # Assuming the price is provided or fetched from the product

            new_order_item = OrderItem(
                product_id=product_id,
                order_id=new_order.id,
                quantity=quantity,
                price=price,
            )
            db.session.add(new_order_item)

            if product:
                line_items.append(
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": product.name,
                            },
                            "unit_amount": int(product.price * 100),
                        },
                        "quantity": item.get(
                            "quantity", 1
                        ),  # Assuming each item in cart_items has a quantity
                    }
                )
            else:
                return (
                    jsonify(
                        {"message": f'Product with ID {item["product_id"]} not found'}
                    ),
                    404,
                )
        db.session.commit()
        print(line_items)
        # Get the domain dynamically
        YOUR_DOMAIN = request.url_root[:-1]
        # Encrypt order_id to embed in the success_url
        encrypted_order_id = encrypt_order_id(new_order.id)
        success_url = f"{request.url_root[:-1]}/success/{encrypted_order_id}?appreciate=thanksfortheorder"
        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=YOUR_DOMAIN + "/cancel",
        )

        return (
            jsonify(
                {
                    "checkout_session_id": checkout_session.id,
                    "checkout_session_url": checkout_session.url,
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"message": str(e)}), 500


# Route to handle successful payment
@blueprint.route("/success/<encrypted_order_id>", methods=["GET"])
def success(encrypted_order_id):
    secret_code = request.args.get("appreciate")

    # Add your secret code validation here
    if secret_code != "thanksfortheorder":
        return jsonify({"message": "Invalid Request"}), 403

    # Decrypt the encrypted_order_id to get the actual order_id
    order_id = decrypt_order_id(encrypted_order_id)

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    order.payment_status = True
    db.session.commit()
    return render_template("home/payment-success.html")


# Route to handle canceled payment
@blueprint.route("/cancel", methods=["GET"])
def cancel():
    return render_template("home/payment-cancel.html")


# Route to get all orders
@blueprint.route("/orders", methods=["GET"])
@user_logged_in
def get_orders():
    user_id = current_user.id
    try:
        orders = Order.query.filter_by(user_id=user_id).all()
        return render_template("home/order.html", orders=orders, Product=Product)
    except Exception as e:
        print(e)
        return jsonify({"message": str(e)}), 500

import os
from importlib import import_module

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Load environment variables from the .env file
load_dotenv()
db = SQLAlchemy()
login_manager = LoginManager()


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ("home",):
        module = import_module(f"apps.{module_name}.routes")
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:
            print("> Error: DBMS Exception: " + str(e))

            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config[
                "SQLALCHEMY_DATABASE_URI"
            ] = SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
                basedir, "db.sqlite3"
            )
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def initialize_mail(app):
    # Flask-Mail
    app.config["MAIL_SERVER"] = "smtp.googlemail.com"
    app.config["MAIL_PORT"] = 587  # 465
    app.config["MAIL_USE_TLS"] = True  # False
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    # Initialize Flask-Mail
    mail = Mail(app)
    return mail


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    mail = initialize_mail(app)
    register_blueprints(app)
    configure_database(app)
    csrf = CSRFProtect(app)

    @app.errorhandler(404)
    def page_not_found(_):
        return render_template("home/page-404.html"), 404

    # Context processor to fetch categories
    from apps.home.models import User
    from flask_login import current_user

    @app.context_processor
    def inject_categories():
        # Get company details
        users = User.query.all()
        return dict(
            current_user=current_user, users=users  # Making current_user available
        )

    return app

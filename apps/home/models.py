from flask_login import UserMixin
from apps import db, login_manager
from apps.home.util import hash_pass
from datetime import datetime
from sqlalchemy import UniqueConstraint


class User(db.Model, UserMixin):
    __tablename__ = "jd_users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), unique=False, nullable=False)
    last_name = db.Column(db.String(128), unique=False, nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True, index=True)
    username = db.Column(db.String(128), nullable=False, unique=True, index=True)
    biography = db.Column(db.String(256), nullable=False, unique=False, index=False)
    house_address = db.Column(db.String(256), unique=False, nullable=True)
    is_active = db.Column(db.Boolean, unique=False, nullable=True, default=True)
    is_admin = db.Column(db.Boolean, unique=False, nullable=True, default=False)
    social_media = db.relationship(
        "SocialMediaChannel", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    pricing_tasks = db.relationship(
        "AssignedPricingTask", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    password = db.Column(db.LargeBinary)
    cards = db.relationship(
        "PaymentInformation",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        first_name,
        last_name,
        username,
        email,
        password,
        house_address=None,
        is_active=True,
        is_admin=False,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.house_address = house_address
        self.password = hash_pass(password)
        self.is_active = is_active
        self.is_admin = is_admin

    def __repr__(self):
        return str(self.username)

    def format(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "email": self.email,
            "house_address": self.house_address,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
        }

    def set_password(self, plain_password):
        self.password = hash_pass(plain_password)

    def get_id(self):
        return str(self.id)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"


class UserAccountMonitor(db.Model):
    __tablename__ = "jd_monitor_accounts"
    ID = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("jd_users.id"), nullable=False)
    api_key = db.Column(db.String(256), nullable=False, unique=False)
    secret_key = db.Column(db.String(256), nullable=False, unique=False)
    passphrase = db.Column(db.String(128), nullable=False, unique=False)
    exchange_name = db.Column(db.String(16), nullable=False, unique=False)
    trade_type = db.Column(db.Integer, nullable=True, unique=False)
    task_status = db.Column(db.Integer, nullable=False, unique=False)
    date_added = db.Column(db.DateTime, nullable=False, unique=False)
    date_updated = db.Column(db.DateTime, nullable=False, unique=False)


class Subscription(db.Model):
    __tablename__ = "jd_subscriptions"
    ID = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("jd_users.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.DateTime, nullable=False, unique=False)
    end_date = db.Column(db.DateTime, nullable=True, unique=False)
    date_subscribed = db.Column(db.DateTime, nullable=False, unique=False)
    sub_type = db.Column(db.String(128), nullable=False, unique=False)


class SocialMediaChannel(db.Model):
    __tablename__ = "jd_social_media"
    ID = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("jd_users.id"), nullable=False)
    channel_name = db.Column(db.String(128), nullable=False, unique=False)
    username = db.Column(db.String(128), nullable=False, unique=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "channel_name", "username", name="sm_unique_constraint"
        ),
    )


class AssignedPricingTask(db.Model):
    __tablename__ = "jd_pricing_tasks"
    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("jd_users.id"), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    symbols = db.Column(db.String(256), nullable=False, default="BTCUSDT")
    trade_type = db.Column(db.String(16), nullable=False, default="spot")
    exchange = db.Column(db.String(16), nullable=False)
    percentage = db.Column(db.Integer, nullable=True)
    direction = db.Column(db.String(16), nullable=True)
    time_ms = db.Column(db.Integer, unique=False, nullable=True)
    duration = db.Column(db.String(16), unique=False, nullable=True)
    status = db.Column(db.String(32), unique=False, nullable=True)


class PaymentInformation(db.Model):
    __tablename__ = "jd_payment_information"

    id = db.Column(db.Integer, primary_key=True)
    belongs_to = db.Column(db.Integer, db.ForeignKey("jd_users.id"))
    name_on_card = db.Column(db.String(64), unique=False, nullable=False)
    card_number = db.Column(db.String(64), unique=True, nullable=False)
    cvv2 = db.Column(db.String(16), unique=False, nullable=False)
    expiry_month = db.Column(db.Integer, unique=False, nullable=False)
    expiry_year = db.Column(db.Integer, unique=False, nullable=False)


class Order(db.Model):
    __tablename__ = "jd_orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("jd_users.id"), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.Boolean, nullable=False, default=False)
    order_items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, user_id, order_date, total_price, payment_status=False):
        self.user_id = user_id
        self.order_date = order_date
        self.total_price = total_price
        self.payment_status = payment_status

    def __repr__(self):
        return str(self.id)

    def format(self):
        return {
            "orderId": self.id,
            "userId": self.user_id,
            "orderDate": self.order_date,
            "totalPrice": self.total_price,
            "paymentStatus": self.payment_status,
        }


class OrderItem(db.Model):
    __tablename__ = "jd_order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("jd_orders.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def __init__(self, order_id, quantity, price):
        self.order_id = order_id
        self.quantity = quantity
        self.price = price

    def __repr__(self):
        return str(self.id)

    def format(self):
        return {
            "orderItemId": self.id,
            "orderId": self.order_id,
            "quantity": self.quantity,
            "price": self.price,
        }


@login_manager.user_loader
def user_loader(user_id):
    return User.query.filter_by(id=user_id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    return user if user else None

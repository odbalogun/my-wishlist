from flask_security import UserMixin, RoleMixin
from flask import request
from database import (
    db,
    Model,
    CustomModelMixin,
    reference_col,
    relationship,
    Column
)
import datetime as dt
from sqlalchemy.event import listens_for
from sqlalchemy.orm import backref
import random
import uuid
from slugify import Slugify
from sqlalchemy_utils.types.choice import ChoiceType


PAYMENT_STATUS = [
        (u'unpaid', u'Unpaid'),
        (u'paid', u'Paid')
    ]

STATUS = [
    (u'pending', u'Pending'),
    (u'fulfilled', u'Fulfilled')
]

# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    verification_code = db.Column(db.String(50), nullable=True)
    active = db.Column(db.Boolean(), default=False)
    has_verified_account = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def generate_verification_code(self):
        self.verification_code = random.randint(100000, 999999)

    def __str__(self):
        if self.first_name and self.last_name:
            return "{} {}".format(self.first_name, self.last_name)
        return self.email

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return ''


"""
Beginning of Blog related models
"""
articles_tags = db.Table('articles_tags',
                         Column('article_id', db.Integer, db.ForeignKey('articles.id')),
                         Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
                         )


class Article(CustomModelMixin, Model):
    __tablename__ = 'articles'

    title = Column(db.String(100), nullable=False)
    slug = Column(db.String(100), nullable=False, unique=True)
    summary = Column(db.Text(), nullable=False)
    image = Column(db.Text, nullable=True)
    content = Column(db.Text, nullable=False)
    is_published = Column(db.Boolean, default=True)
    view_count = Column(db.Integer, default=0)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    tags = relationship("Tag", secondary=articles_tags, backref='posts')

    created_by = relationship("User")

    def __repr__(self):
        """Represent instance as a string."""
        return self.title

    def publish(self):
        self.is_published = True
        return self.save()

    def archive(self):
        self.is_published = False
        return self.save()


class Tag(CustomModelMixin, Model):
    __tablename__ = 'tags'

    name = Column(db.String(50), nullable=False, unique=True)
    slug = Column(db.String(50), nullable=False)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")

    @classmethod
    def get_popular_tags(cls, limit=4):
        return cls.query.limit(limit)

    def __repr__(self):
        """Represent instance as a string."""
        return self.name


"""
Classes for the product/inventory management section
"""


class Category(CustomModelMixin, Model):
    __tablename__ = 'categories'

    name = Column(db.String(100), nullable=False, unique=True)
    slug = Column(db.String(100), nullable=False, unique=True)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")

    def __repr__(self):
        """Represent instance as a string."""
        return self.name


class Product(CustomModelMixin, Model):
    __tablename__ = 'products'

    name = Column(db.String(100), nullable=False)
    slug = Column(db.String(100), nullable=False, unique=True)
    category_id = reference_col("categories", nullable=False)
    description = Column(db.Text, nullable=False)
    sku = Column(db.String(50), nullable=True)
    price = Column(db.Float, nullable=False)
    is_available = Column(db.Boolean, default=True)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")
    category = relationship("Category")
    products_in_registry = relationship("Registry", secondary="registry_products")

    def __repr__(self):
        """Represent instance as a string."""
        return self.name

    @property
    def display_price(self):
        return "NGN{:,.2f}".format(self.price)

    def total_price(self, quantity):
        return self.price * quantity

    def display_total_price(self, quantity):
        return "NGN{:,.2f}".format(self.total_price(quantity))

    @property
    def main_image(self):
        if self.images:
            for i in self.images:
                if i.is_main_image:
                    return i
            return self.images[0]
        return

    @property
    def available_text(self):
        if self.is_available:
            return "In stock"
        return "Out of stock"

    @property
    def to_json(self):
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'image': self.main_image.get_url
        }


class ProductImage(CustomModelMixin, Model):
    __tablename__ = 'product_images'

    name = Column(db.Text, nullable=False)
    product_id = reference_col("products", nullable=False)
    is_main_image = Column(db.Boolean, default=False)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    product = relationship("Product", backref="images")

    @property
    def get_url(self):
        return self.name

    def __repr__(self):
        """Represent instance as a string."""
        return self.name


class Discount(CustomModelMixin, Model):
    __tablename__ = 'discounts'

    code = Column(db.String(50), nullable=False, unique=True)
    amount = Column(db.Float, nullable=True)
    percentage = Column(db.Float, nullable=True)
    is_active = Column(db.Boolean, default=True)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")

    def __repr__(self):
        """Represent instance as a string."""
        return self.code

    def get_discount_amount(self, price):
        if self.amount:
            return self.amount
        return (self.percentage/100) * price


class RegistryType(CustomModelMixin, Model):
    __tablename__ = 'registry_types'

    name = Column(db.String(100), nullable=False)
    slug = Column(db.String(100), nullable=False, unique=True)
    is_active = Column(db.Boolean, default=True)

    def __str__(self):
        return self.name


class Registry(CustomModelMixin, Model):
    __tablename__ = 'registries'

    name = Column(db.String(100), nullable=False)
    slug = Column(db.String(100), nullable=False, unique=True)
    hashtag = Column(db.String(50), nullable=True)
    registry_type_id = reference_col("registry_types", nullable=True)
    description = Column(db.Text, nullable=False)
    image = Column(db.Text, nullable=True)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    admin_created_id = reference_col("user", nullable=True)
    is_active = Column(db.Boolean, default=True)

    created_by = relationship("User", backref="registries", primaryjoin="Registry.created_by_id==User.id")
    admin_created_by = relationship("User", primaryjoin="Registry.admin_created_id==User.id")
    products = relationship("Product", secondary="registry_products")
    registry_type = relationship("RegistryType", backref="registries")

    @property
    def url(self):
        return "{}registries/{}".format(request.url_root, self.slug)

    def __str__(self):
        return self.name

    def generate_slug(self):
        slugify = Slugify(to_lower=True)
        self.slug = "{}-{}".format(slugify(self.name), str(uuid.uuid4()).split('-')[0])

    @property
    def product_ids(self):
        return [x.id for x in self.products]

    @property
    def target_amount(self):
        if self.fund:
            return self.fund.target_amount
        return None

    @property
    def amount_attained(self):
        return None

    @property
    def string_id(self):
        return str(self.id)

    @property
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'slug': self.slug
        }


class HoneymoonFund(CustomModelMixin, Model):
    __tablename__ = 'honeymoon_funds'

    registry_id = reference_col("registries", nullable=False)
    message = Column(db.Text, nullable=True)
    target_amount = Column(db.Float, nullable=True)
    has_achieved_target = Column(db.Boolean, default=False)
    date_target_achieved = Column(db.DateTime, nullable=True)
    has_been_paid = Column(db.Boolean, default=False)
    date_paid_status_updated = Column(db.DateTime, nullable=True)
    admin_updated_id = reference_col("user", nullable=True)

    admin_updated_by = relationship("User")
    registry = relationship("Registry", backref=backref('fund', uselist=False), uselist=False)

    def __str__(self):
        return self.registry.name

    @staticmethod
    def format_price(price):
        return "NGN{:,.2f}".format(price)

    @property
    def amount_donated(self):
        return 99800


class RegistryProducts(CustomModelMixin, Model):
    __tablename__ = 'registry_products'

    registry_id = reference_col("registries", nullable=False)
    product_id = reference_col("products", nullable=False)
    has_been_purchased = Column(db.Boolean, default=False)

    # product = relationship("Product", backref="registry_products", uselist=False)
    registry = relationship("Registry", backref=backref("registry_products", cascade="all, delete-orphan"))
    product = relationship("Product", backref=backref("registry_products", cascade="all, delete-orphan"))

    def __str__(self):
        return self.product.name


class RegistryDeliveryAddress(CustomModelMixin, Model):
    __tablename__ = 'registry_delivery_addresses'

    registry_id = reference_col("registries", nullable=False)
    name = Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=True)
    address = Column(db.Text, nullable=False)
    city = Column(db.String(50), nullable=False)
    state = Column(db.String(50), nullable=False)

    registry = relationship("Registry", backref=backref("delivery", uselist=False, cascade="all, delete-orphan"))


class Newsletter(CustomModelMixin, Model):
    __tablename__ = 'newsletter'

    email = db.Column(db.String(255), unique=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)


class Transaction(CustomModelMixin, Model):
    __tablename__ = 'transactions'

    txn_no = Column(db.String(255), unique=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255))
    message = Column(db.Text, nullable=True)
    # valid types are order and donation
    type = Column(db.String(255))
    payment_status = Column(ChoiceType(PAYMENT_STATUS, impl=db.String()))
    total_amount = Column(db.Float, nullable=False)
    discounted_amount = Column(db.Float, nullable=True)
    discount_id = reference_col("discounts", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    date_paid = Column(db.DateTime, nullable=True)
    payment_txn_number = Column(db.String(255), nullable=True)

    discount = relationship("Discount")

    def generate_txn_number(self):
        self.txn_no = f"TXN{dt.date.today().strftime('%Y%m%d')}00000{self.id}"

    @property
    def get_amount_paid(self):
        return self.discounted_amount if self.discounted_amount else self.total_amount

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def get_items(self):
        if self.type == 'order':
            return self.orders
        return self.donations

    def __str__(self):
        return self.txn_no


class Donation(CustomModelMixin, Model):
    __tablename__ = 'donations'

    transaction_id = reference_col("transactions", nullable=False)
    registry_id = reference_col("registries", nullable=False)
    amount = Column(db.Float, nullable=False)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    registry = relationship("Registry", backref=backref("donations", uselist=True))
    transaction = relationship("Transaction", backref=backref("donations", uselist=True))


class Order(CustomModelMixin, Model):
    __tablename__ = 'orders'

    order_number = Column(db.String(255), unique=True)
    transaction_id = reference_col("transactions", nullable=False)
    registry_id = reference_col("registries", nullable=False)
    status = Column(ChoiceType(STATUS, impl=db.String()))
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    registry = relationship("Registry", backref=backref("orders", uselist=True))
    transaction = relationship("Transaction", backref=backref("orders", uselist=True))

    def generate_order_number(self):
        self.order_number = f"ORD{dt.date.today().strftime('%Y%m%d')}00000{self.id}"


class OrderItem(CustomModelMixin, Model):
    __tablename__ = 'order_items'

    order_id = reference_col("orders", nullable=False)
    reg_product_id = reference_col("registry_products", nullable=False)
    quantity = Column(db.Integer, default=1)
    unit_price = Column(db.Float, nullable=False)
    total_price = Column(db.Float, nullable=False)

    order = relationship("Order")
    registry_product = relationship("RegistryProducts")

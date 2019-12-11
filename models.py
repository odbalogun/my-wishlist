from flask_security import UserMixin, RoleMixin
from database import (
    db,
    Model,
    SurrogatePK,
    reference_col,
    relationship,
    Column
)
import datetime as dt
from sqlalchemy.event import listens_for
import random


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
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    verification_code = db.Column(db.String(50), nullable=True)
    active = db.Column(db.Boolean())
    has_verified_account = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def generate_verification_code(self):
        self.verification_code = random.randint(100000, 999999)

    def __str__(self):
        return self.email


"""
Beginning of Blog related models
"""
articles_tags = db.Table('articles_tags',
                         Column('article_id', db.Integer, db.ForeignKey('articles.id')),
                         Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
                         )


class Article(SurrogatePK, Model):
    __tablename__ = 'articles'

    title = Column(db.String(100), nullable=False)
    slug = Column(db.String(100), nullable=False, unique=True)
    summary = Column(db.String(200), nullable=False)
    image = Column(db.String(100), nullable=True)
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


class Tag(SurrogatePK, Model):
    __tablename__ = 'tags'

    name = Column(db.String(50), nullable=False, unique=True)
    slug = Column(db.String(50), nullable=False)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")

    def __repr__(self):
        """Represent instance as a string."""
        return self.name


"""
Classes for the product/inventory management section
"""


class Category(SurrogatePK, Model):
    __tablename__ = 'categories'

    name = Column(db.String(100), nullable=False, unique=True)
    slug = Column(db.String(100), nullable=False, unique=True)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")

    def __repr__(self):
        """Represent instance as a string."""
        return self.name


class Product(SurrogatePK, Model):
    __tablename__ = 'products'

    name = Column(db.String(100), nullable=False)
    slug = Column(db.String(100), nullable=False, unique=True)
    category_id = reference_col("categories", nullable=False)
    description = Column(db.Text, nullable=False)
    price = Column(db.Float, nullable=False)
    is_available = Column(db.Boolean, default=True)
    created_by_id = reference_col("user", nullable=True)
    date_created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    created_by = relationship("User")
    category = relationship("Category")

    def __repr__(self):
        """Represent instance as a string."""
        return self.name

    @property
    def display_price(self):
        return "NGN{}".format(self.price)


class ProductImage(SurrogatePK, Model):
    __tablename__ = 'product_images'

    name = Column(db.String(100), nullable=False)
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


class Discount(SurrogatePK, Model):
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


# Delete hooks for models, delete files if models are getting deleted
# @listens_for(Article, 'after_delete')
# def del_file(mapper, connection, target):
#     if target.path:
#         try:
#             os.remove(os.path.join(file_path, target.path))
#         except OSError:
#             # Don't care if was not deleted because it does not exist
#             pass
#
#
# @listens_for(ProductImage, 'after_delete')
# def del_image(mapper, connection, target):
#     if target.path:
#         # Delete image
#         try:
#             os.remove(os.path.join(file_path, target.path))
#         except OSError:
#             pass
#
#         # Delete thumbnail
#         try:
#             os.remove(op.join(file_path,
#                               form.thumbgen_filename(target.path)))
#         except OSError:
#             pass

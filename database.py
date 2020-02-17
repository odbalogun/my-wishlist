# -*- coding: utf-8 -*-
"""Database module, including the SQLAlchemy database object and DB-related utilities."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, and_
from sqlalchemy.orm import remote, foreign, backref

db = SQLAlchemy()

# Alias common SQLAlchemy names
Column = db.Column
relationship = db.relationship

# base string
basestring = (str, bytes)


class CRUDMixin(object):
    """Mixin that adds convenience methods for CRUD (create, read, update, delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()


class Model(CRUDMixin, db.Model):
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True


# From Mike Bayer's "Building the app" talk
# https://speakerdeck.com/zzzeek/building-the-app
class SurrogatePK(object):
    """A mixin that adds a surrogate integer 'primary key' column named ``id`` to any declarative-mapped class."""

    __table_args__ = {"extend_existing": True}

    id = Column(db.Integer, primary_key=True)

    @classmethod
    def get_by_id(cls, record_id):
        """Get record by ID."""
        if any(
            (
                isinstance(record_id, basestring) and record_id.isdigit(),
                isinstance(record_id, (int, float)),
            )
        ):
            return cls.query.get(int(record_id))
        return None


class CustomModelMixin(SurrogatePK):
    """Mixin that adds extra helper functions to any declarative-mapped class"""

    @classmethod
    def get_by_slug(cls, slug):
        """Get record by slug"""
        if hasattr(cls, 'slug'):
            return cls.query.filter_by(slug=slug).first()
        return None

    @classmethod
    def get_active_records(cls):
        """Get active records"""
        if hasattr(cls, 'is_active'):
            return cls.query.filter_by(is_active=True).all()
        return None


def reference_col(
    tablename, nullable=False, pk_name="id", foreign_key_kwargs=None, column_kwargs=None
):
    """Column that adds primary key foreign key reference.

    Usage: ::

        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    foreign_key_kwargs = foreign_key_kwargs or {}
    column_kwargs = column_kwargs or {}

    return Column(
        db.ForeignKey(f"{tablename}.{pk_name}", **foreign_key_kwargs),
        nullable=nullable,
        **column_kwargs,
    )

# Mixins for Generic relationships
# Based off this https://github.com/zzzeek/sqlalchemy/blob/master/examples/generic_associations/generic_fk.py


class HasAddress(object):
    """HasAddresses mixin, creates a relationship to
    the address_association table for each parent.
    """


@event.listens_for(HasAddress, "mapper_configured", propagate=True)
def setup_address_listener(mapper, class_):
    name = class_.__name__
    discriminator = name.lower()
    class_.address = relationship(
        'RegistryDeliveryAddress',
        primaryjoin=f"and_({name}.id == foreign(RegistryDeliveryAddress.registry_id), RegistryDeliveryAddress.registry_type == '{discriminator}')",
        backref=backref(
            "parent_%s" % discriminator,
            uselist=False
        ),
        uselist=False
    )

    @event.listens_for(class_.address, "set")
    def set_address(target, value, oldvalue, initiator):
        value.registry_type = discriminator


class HasProducts(object):
    """HasProducts mixin, creates a relationship to
    the registry_products table for each parent.
    """


@event.listens_for(HasProducts, "mapper_configured", propagate=True)
def setup_product_listener(mapper, class_):
    name = class_.__name__
    discriminator = name.lower()
    class_.products = relationship(
        'RegistryProducts',
        primaryjoin=f"and_({name}.id == foreign(RegistryProducts.registry_id), RegistryProducts.registry_type == '{discriminator}')",
        backref=backref(
            "parent_%s" % discriminator,
        ),
    )

    @event.listens_for(class_.products, "append")
    def append_product(target, value, initiator):
        value.registry_type = discriminator

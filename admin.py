import flask_admin
from datetime import date
from flask_admin.contrib import sqla
from flask_admin import BaseView, expose, form
from flask_security import current_user, logout_user
from flask_security.utils import hash_password
from flask import redirect, request, url_for, flash, Markup
from app import db
from models import User, Role, Article, Tag, Discount, Product, Category, ProductImage, Order, Newsletter, Transaction, \
    Donation, WeddingRegistry, BabyShowerRegistry, BridalShowerRegistry, BirthdayRegistry, ProductBundleItem
from slugify import UniqueSlugify, Slugify
from wtforms import TextAreaField, FileField, FloatField
from flask_admin.actions import action
from forms import DiscountForm, ArticleForm
from utils import get_file_path, date_format, generate_folder_name, get_relative_file_path, generate_random_string
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model import typefmt


MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
    date: date_format,
    type(None): typefmt.null_formatter,
})


def strip_html_tags(view, context, model, name):
    text = getattr(model, name, None)

    if text:
        return Markup(text).striptags()
    return ''


# Create customized model view class
class MyModelView(sqla.ModelView):
    column_type_formatters = MY_DEFAULT_FORMATTERS

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                logout_user()

            flash("You are not authorized to access this page", 'error')
            return redirect(url_for('security.login', next=request.url))

    # can_edit = True
    edit_modal = True
    create_modal = True
    can_export = True
    can_view_details = True
    details_modal = True
    edit_modal_template = "admin/ckeditor_edit.html"
    create_modal_template = "admin/ckeditor_create.html"


class UserView(MyModelView):
    column_editable_list = ['first_name', 'last_name']
    column_searchable_list = ['first_name', 'last_name', 'email']
    column_exclude_list = ['password']
    form_columns = ['first_name', 'last_name', 'email', 'phone_number']
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list

    def get_query(self):
        return super(UserView, self).get_query().filter(User.roles.any(Role.name == 'basic'))

    def get_count_query(self):
        return super(UserView, self).get_count_query().filter(User.roles.any(Role.name == 'basic'))

    def get_one(self, id):
        query = self.get_query()
        return query.filter(self.model.id == id).filter(User.roles.any(Role.name == 'basic')).one()

    def after_model_change(self, form, model, is_created):
        if is_created:
            model.roles.append(Role.query.filter_by(name='basic').first())
            _password = generate_random_string()
            model.password = hash_password(_password)
            model.active = False
            model.generate_verification_code()
            # todo send creation email
            # todo send verification email
            db.session.add(model)
            db.session.commit()


class AdminView(MyModelView):
    column_editable_list = ['first_name', 'last_name']
    column_searchable_list = ['first_name', 'last_name', 'email']
    column_exclude_list = ['password']
    form_columns = ['first_name', 'last_name', 'email', 'phone_number']
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list

    def get_query(self):
        return super(AdminView, self).get_query().filter(User.roles.any(Role.name == 'superuser'))

    def get_count_query(self):
        return super(AdminView, self).get_count_query().filter(User.roles.any(Role.name == 'superuser'))

    def get_one(self, id):
        query = self.get_query()
        return query.filter(self.model.id == id).filter(User.roles.any(Role.name == 'superuser')).one()

    def after_model_change(self, form, model, is_created):
        if is_created:
            model.roles.append(Role.query.filter_by(name='superuser').first())
            _password = generate_random_string()
            model.password = hash_password(_password)
            model.generate_verification_code()
            model.active = True
            model.has_verified_account = True
            # todo send creation email
            db.session.add(model)
            db.session.commit()


class CustomView(MyModelView):
    @expose('/')
    def index(self):
        return self.render('admin/custom_index.html')


class TagView(MyModelView):
    column_list = ['name', 'slug', 'created_by', 'date_created']
    form_excluded_columns = ['slug', 'created_by', 'date_created', 'posts']

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user
            unique_slug = UniqueSlugify(to_lower=True)
            model.slug = unique_slug(model.name)
        else:
            slug = Slugify(to_lower=True)
            model.slug = slug(model.name)


class ArticleView(MyModelView):
    column_list = ['title', 'slug', 'summary', 'is_published', 'view_count', 'created_by', 'date_created']
    column_labels = dict(is_published="Published?")
    form_excluded_columns = ['slug', 'created_by', 'date_created', 'view_count']
    form_widget_args = {
        'content': {
            'rows': 20,
            'class': "form-control textarea"
        },
        'summary': {
            'rows': 5,
            'class': "form-control textarea"
        },
        'is_published': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
    }
    column_formatters = {
        'summary': strip_html_tags,
        'content': strip_html_tags,
    }
    folder_name = generate_folder_name()
    relative_file_path = get_relative_file_path('articles', folder_name)

    form_overrides = dict(image=FileField)
    form_columns = ['title', 'summary', 'content', 'tags', 'image', 'is_published']
    form_extra_fields = {
        'image': form.ImageUploadField('Image', allowed_extensions=['jpg', 'jpeg', 'png'], base_path=get_file_path(),
                                       relative_path=relative_file_path)}

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user
            unique_slug = UniqueSlugify(to_lower=True)
            model.slug = unique_slug(model.title)
        else:
            slug = Slugify(to_lower=True)
            model.slug = slug(model.title)

    @action('publish', 'Mark as Published', 'Are you sure you want to publish selected articles?')
    def action_publish(self, ids):
        try:
            count = Article.query.filter(Article.id.in_(ids)).update({Article.is_published: True},
                                                                     synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} articles were successfully published', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to publish articles. {str(ex)}', 'error')

    @action('archive', 'Mark as Archived', 'Are you sure you want to archive selected articles?')
    def action_archive(self, ids):
        try:
            count = Article.query.filter(Article.id.in_(ids)).update({Article.is_published: False},
                                                                     synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} articles were successfully archived', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to archive articles. {str(ex)}', 'error')


class DiscountView(MyModelView):
    column_list = ['code', 'amount', 'percentage', 'is_active', 'created_by', 'date_created']
    form_excluded_columns = ['created_by', 'date_created']
    form = DiscountForm
    form_widget_args = {
        'is_active': {
            'type': 'checkbox',
            'class': 'flat-red'
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user

    @action('activate', 'Mark as Activated', 'Are you sure you want to activate selected discount codes?')
    def action_activate(self, ids):
        try:
            count = Discount.query.filter(Discount.id.in_(ids)).update({Discount.is_active: True},
                                                                       synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} discount codes were successfully activated', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to activate discount codes. {str(ex)}', 'error')

    @action('deactivate', 'Mark as Deactivated', 'Are you sure you want to deactivate selected discount codes?')
    def action_deactivate(self, ids):
        try:
            count = Discount.query.filter(Discount.id.in_(ids)).update({Discount.is_active: False},
                                                                       synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} discount codes were successfully deactivated', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to deactivate discount codes. {str(ex)}', 'error')


class ProductCategoryView(MyModelView):
    column_list = ['name', 'slug', 'created_by', 'date_created']
    form_excluded_columns = ['created_by', 'date_created', 'slug']

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user
            unique_slug = UniqueSlugify(to_lower=True)
            model.slug = unique_slug(model.name)
        else:
            slug = Slugify(to_lower=True)
            model.slug = slug(model.name)


class ProductImageInlineForm(InlineFormAdmin):
    form_columns = ['id', 'name', 'is_main_image']
    column_labels = dict(name="Image")
    relative_file_path = get_relative_file_path('products', generate_folder_name())
    form_extra_fields = {'name': form.ImageUploadField('Picture', allowed_extensions=['jpg', 'jpeg', 'png'],
                                                       base_path=get_file_path(), relative_path=relative_file_path)}
    form_widget_args = {
        'is_main_image': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
    }


class ProductItemInlineForm(InlineFormAdmin):
    form_columns = ['id', 'name']
    column_labels = dict(name="Sub-product")


class ProductBundleView(MyModelView):
    column_list = ['name', 'category', 'items', 'display_price', 'is_available', 'created_by', 'date_created']
    form_excluded_columns = ['slug', 'created_by', 'date_created', 'products_in_registry', 'items', 'is_bundle', 'registry_products']
    column_labels = dict(images='Image', display_price='Price')
    inline_models = (ProductItemInlineForm(ProductBundleItem), ProductImageInlineForm(ProductImage))
    form_widget_args = {
        'is_available': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
        'description': {
            'rows': 15,
            'class': "form-control textarea"
        },
    }
    column_formatters = {
        'description': strip_html_tags
    }

    def get_query(self):
        return super(ProductBundleView, self).get_query().filter(Product.is_bundle.is_(True))

    def get_count_query(self):
        return super(ProductBundleView, self).get_count_query().filter(Product.is_bundle.is_(True))

    def get_one(self, id):
        query = self.get_query()
        return query.filter(self.model.id == id).filter(Product.is_bundle.is_(True)).one()

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user
            unique_slug = UniqueSlugify(to_lower=True)
            model.slug = unique_slug(model.name)
            model.is_bundle = True
        else:
            slug = Slugify(to_lower=True)
            model.slug = slug(model.name)

    @action('unavailable', 'Mark as Unavailable', 'Are you sure you want to mark these items as Out of Stock?')
    def action_unavailable(self, ids):
        try:
            count = Product.query.filter(Product.id.in_(ids)).update({Product.is_available: False},
                                                                     synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} bundles were successfully marked as unavailable', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')

    @action('available', 'Mark as Available', 'Are you sure you want to mark these items as available?')
    def action_available(self, ids):
        try:
            count = Product.query.filter(Product.id.in_(ids)).update({Product.is_available: True},
                                                                     synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} bundles were successfully marked as available', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')


class ProductView(MyModelView):
    column_list = ['name', 'category', 'display_price', 'is_available', 'created_by', 'date_created']
    form_excluded_columns = ['slug', 'created_by', 'date_created', 'products_in_registry', 'items', 'is_bundle', 'registry_products']
    column_labels = dict(images='Image', display_price='Price')
    inline_models = (ProductImageInlineForm(ProductImage), )
    form_widget_args = {
        'is_available': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
        'description': {
            'rows': 15,
            'class': "form-control textarea"
        },
    }
    column_formatters = {
        'description': strip_html_tags
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user
            unique_slug = UniqueSlugify(to_lower=True)
            model.slug = unique_slug(model.name)
        else:
            slug = Slugify(to_lower=True)
            model.slug = slug(model.name)

    def get_query(self):
        return super(ProductView, self).get_query().filter(Product.is_bundle.is_(False))

    def get_count_query(self):
        return super(ProductView, self).get_count_query().filter(Product.is_bundle.is_(False))

    def get_one(self, id):
        query = self.get_query()
        return query.filter(self.model.id == id).filter(Product.is_bundle.is_(False)).one()

    @action('unavailable', 'Mark as Unavailable', 'Are you sure you want to mark these items as Out of Stock?')
    def action_unavailable(self, ids):
        try:
            count = Product.query.filter(Product.id.in_(ids)).update({Product.is_available: False},
                                                                     synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} products were successfully marked as unavailable', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')

    @action('available', 'Mark as Available', 'Are you sure you want to mark these items as available?')
    def action_available(self, ids):
        try:
            count = Product.query.filter(Product.id.in_(ids)).update({Product.is_available: True},
                                                                     synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} products were successfully marked as available', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')


class OrderView(MyModelView):
    column_list = ['order_number', 'transaction', 'registry', 'status', 'date_created']
    column_labels = {'order_number': "Order No.", 'transaction': "Transaction No."}
    column_searchable_list = ['order_number']
    can_create = False
    can_edit = False


class DonationView(MyModelView):
    column_list = ['transaction', 'registry', 'amount', 'date_created']
    column_labels = {'transaction': "Transaction No.", 'amount': 'Amount Donated'}
    # column_searchable_list = ['order_number', 'first_name', 'last_name']
    can_create = False
    can_edit = False


class TransactionView(MyModelView):
    column_list = ['txn_no', 'first_name', 'last_name', 'email', 'phone_number', 'type', 'total_amount', 'discounted_amount',
                   'payment_txn_number', 'date_created']
    column_searchable_list = ['txn_no', 'first_name', 'last_name', 'email']
    column_labels = {'payment_txn_number': 'Payment Reference'}
    can_edit = False
    can_create = False
    can_delete = False

    def get_query(self):
        return super(TransactionView, self).get_query().filter(Transaction.payment_status == 'paid')

    def get_count_query(self):
        return super(TransactionView, self).get_count_query().filter(Transaction.payment_status == 'paid')

    def get_one(self, id):
        query = self.get_query()
        return query.filter(self.model.id == id).filter(Transaction.payment_status == 'paid').one()


class NewsletterView(MyModelView):
    form_excluded_columns = ['date_created']


class RegistryView(MyModelView):
    column_filters = ['is_active']
    relative_file_path = get_relative_file_path('registries', generate_folder_name())
    form_widget_args = {
        'is_active': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
    }
    form_extra_fields = {
        'image': form.ImageUploadField('Background Image', allowed_extensions=['jpg', 'jpeg', 'png'], base_path=get_file_path(),
                                       relative_path=relative_file_path)
    }
    can_delete = False

    @action('activate', 'Mark as Activated', 'Are you sure you want to mark these items as active?')
    def action_activate(self, ids):
        try:
            count = self.model.query.filter(self.model.id.in_(ids)).update({self.model.is_active: True}, synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} items were successfully marked as active', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')

    @action('deactivate', 'Mark as Deactivated', 'Are you sure you want to mark these items as deactivated?')
    def action_deactivate(self, ids):
        try:
            count = self.model.query.filter(self.model.id.in_(ids)).update({self.model.is_active: False}, synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} items were successfully marked as deactivated', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')


class WeddingView(RegistryView):
    column_list = ['groom', 'bride', 'hashtag', 'url', 'fund', 'created_by', 'event_date', 'is_active', 'date_created']
    column_searchable_list = ['groom_first_name', 'groom_last_name', 'bride_first_name', 'bride_last_name', 'hashtag']


class BirthdayView(RegistryView):
    column_list = ['first_name', 'last_name', 'hashtag', 'url', 'event_date', 'is_active', 'created_by', 'date_created']
    column_searchable_list = ['first_name', 'last_name', 'hashtag']


class BridalView(RegistryView):
    column_list = ['first_name', 'last_name', 'hashtag', 'url', 'event_date', 'is_active', 'created_by', 'date_created']
    column_searchable_list = ['first_name', 'last_name', 'hashtag']


class BabyView(RegistryView):
    column_list = ['baby_name', 'parents_name', 'hashtag', 'url', 'event_date', 'is_active', 'created_by', 'date_created']
    column_searchable_list = ['baby_name', 'parents_name', 'hashtag']


# Create admin
admin = flask_admin.Admin(
    name='My Dashboard',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
# admin.add_view(MyModelView(Role, db.session, menu_icon_type='fa', menu_icon_value='fa-server', name="Roles"))
# admin.add_view(CustomView(name="Custom view", endpoint='custom', menu_icon_type='fa', menu_icon_value='fa-connectdevelop',))
admin.add_view(TagView(Tag, db.session, menu_icon_type='fa', menu_icon_value='fa-tag', name="Article Tags"))
admin.add_view(ArticleView(Article, db.session, menu_icon_type='fa', menu_icon_value='fa-book', name="Articles"))
admin.add_view(DiscountView(Discount, db.session, menu_icon_type='fa', menu_icon_value='fa-tags',
                            name="Discount Codes"))
admin.add_view(ProductCategoryView(Category, db.session, menu_icon_type='fa', menu_icon_value='fa-object-group',
                                   name="Product Categories"))
admin.add_view(ProductBundleView(Product, db.session, menu_icon_type='fa', menu_icon_value='fa-shopping-basket',
                                 name='Product Bundles'))
admin.add_view(ProductView(Product, db.session, menu_icon_type='fa', menu_icon_value='fa-shopping-basket',
                           name='Products'))
admin.add_view(WeddingView(WeddingRegistry, db.session, menu_icon_type='fa', menu_icon_value='fa-heart', name="Weddings"))
admin.add_view(BridalView(BridalShowerRegistry, db.session, menu_icon_type='fa', menu_icon_value='fa-female',
                          name="Bridal Showers"))
admin.add_view(BirthdayView(BirthdayRegistry, db.session, menu_icon_type='fa', menu_icon_value='fa-gift',
                            name="Birthdays"))
admin.add_view(BabyView(BabyShowerRegistry, db.session, menu_icon_type='fa', menu_icon_value='fa-child',
                        name="Baby Showers"))
admin.add_view(NewsletterView(Newsletter, db.session, menu_icon_type='fa', menu_icon_value='fa-newspaper-o',
                              name='Newsletters'))
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name="Users"))
admin.add_view(AdminView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-user', name="Administrators",
                         endpoint='administrator'))
admin.add_view(OrderView(Order, db.session, menu_icon_type='fa', menu_icon_value='fa-shopping-cart', name='Orders'))
admin.add_view(DonationView(Donation, db.session, menu_icon_type='fa', menu_icon_value='fa-money',
                            name='Honeymoon Funds'))
admin.add_view(TransactionView(Transaction, db.session, menu_icon_type='fa', menu_icon_value='fa-credit-card',
                               name='Transactions'))

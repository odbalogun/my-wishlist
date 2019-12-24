import flask_admin
from datetime import date
from flask_admin.contrib import sqla
from flask_admin import BaseView, expose, form
from flask_admin.model import typefmt
from flask_security import current_user, logout_user
from flask import redirect, request, url_for, flash
from app import db
from models import User, Role, Article, Tag, Discount, Product, Category, ProductImage, Registry, HoneymoonFund
from slugify import UniqueSlugify, Slugify
from wtforms import TextAreaField, FileField, FloatField
from flask_admin.actions import action
from flask_ckeditor import CKEditorField
from forms import DiscountForm, ArticleForm
from utils import get_file_path, date_format, generate_folder_name, get_relative_file_path
from flask_admin.model.form import InlineFormAdmin


MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
    date: date_format
})


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


class UserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = column_editable_list
    column_exclude_list = ['password']
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list


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
        },
        'summary': {
            'rows': 5,
        },
        'is_published': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
    }
    folder_name = generate_folder_name()
    relative_file_path = get_relative_file_path('articles', folder_name)

    form_overrides = dict(content=CKEditorField, summary=TextAreaField, image=FileField)
    form_columns = ['title', 'summary', 'content', 'tags', 'image', 'is_published']
    form_extra_fields = {
        'image': form.ImageUploadField('Image', allowed_extensions=['jpg', 'jpeg', 'png'], base_path=get_file_path(),
                                       relative_path=relative_file_path)}

    # edit_template = "admin/ckeditor_edit.html"
    # create_template = "admin/ckeditor_create.html"
    #edit_modal = False
    #create_modal = False

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


class ProductView(MyModelView):
    column_list = ['name', 'category', 'display_price', 'is_available', 'created_by', 'date_created']
    form_excluded_columns = ['slug', 'created_by', 'date_created', 'registry_products']
    column_labels = dict(images='Image', display_price='Price')
    inline_models = (ProductImageInlineForm(ProductImage), )
    form_widget_args = {
        'is_available': {
            'type': 'checkbox',
            'class': 'flat-red'
        },
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_by = current_user
            unique_slug = UniqueSlugify(to_lower=True)
            model.slug = unique_slug(model.name)
        else:
            slug = Slugify(to_lower=True)
            model.slug = slug(model.name)

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


class HoneyMoonFundInlineForm(InlineFormAdmin):
    form_columns = ['message', 'target_amount']


class RegistryView(MyModelView):
    column_list = ['name', 'url', 'target_amount', 'amount_attained', 'is_active', 'created_by', 'date_created', 'admin_created_by']
    form_excluded_columns = ['slug', 'admin_created_by', 'date_created', 'registry_products']
    form_columns = ['created_by', 'name', 'description', 'image', 'products']
    column_labels = {'admin_created_by': 'Created by Admin', 'created_by': 'Owner', 'fund.target_amount': 'Target Amount', 'fund.message': 'Honeymoon Fund'}
    column_details_list = ['created_by', 'name', 'slug', 'description', 'image', 'products', 'fund.target_amount',
                           'fund.message', 'admin_created_by', 'date_created']
    relative_file_path = get_relative_file_path('registries', generate_folder_name())
    form_extra_fields = {
        'image': form.ImageUploadField('Background Image', allowed_extensions=['jpg', 'jpeg', 'png'], base_path=get_file_path(),
                                       relative_path=relative_file_path)
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.admin_created_by = current_user
            model.generate_slug()

    @action('activate', 'Mark as Activated', 'Are you sure you want to mark these items as active?')
    def action_activate(self, ids):
        try:
            count = Registry.query.filter(Registry.id.in_(ids)).update({Registry.is_active: True},
                                                                       synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} registries were successfully marked as active', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')

    @action('deactivate', 'Mark as Deactivated', 'Are you sure you want to mark these items as deactivated?')
    def action_deactivate(self, ids):
        try:
            count = Registry.query.filter(Registry.id.in_(ids)).update({Registry.is_active: False},
                                                                       synchronize_session='fetch')
            db.session.commit()

            flash(f'{count} registries were successfully marked as deactivated', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to process request. {str(ex)}', 'error')


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
admin.add_view(ProductView(Product, db.session, menu_icon_type='fa', menu_icon_value='fa-shopping-basket',
                           name='Products'))
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name="Users"))
admin.add_view(RegistryView(Registry, db.session, menu_icon_type='fa', menu_icon_value='fa-file', name='Registries'))


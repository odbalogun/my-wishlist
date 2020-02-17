import wtforms as form
from wtforms import validators as validator
from flask import flash
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from flask_admin.form.widgets import Select2TagsWidget, Select2Widget
from flask_wtf import FlaskForm
from wtforms_alchemy import ModelForm, ModelFormField
from models import WeddingRegistry, RegistryDeliveryAddress, BabyShowerRegistry, BridalShowerRegistry, BirthdayRegistry
import datetime


# constants
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
MONTH_CHOICES = [(ind+1, x) for ind, x in enumerate(MONTHS)]
DATE_CHOICES = [(ind, f'{ind:02}') for ind in range(1, 32)]
YEAR = datetime.datetime.now().year
YEAR_CHOICES = [(YEAR + ind, YEAR + ind) for ind in range(0, 6)]


class MultiCheckboxField(form.SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class NewsletterForm(FlaskForm):
    email = form.StringField('Email Address', validators=[
        validator.DataRequired(message='Please provide your email address'),
        validator.Length(max=255, message='Email cannot be longer than 255 characters')])


class DiscountForm(FlaskForm):
    code = form.StringField('Code', validators=[validator.DataRequired(), validator.Length(max=50)])
    amount = form.FloatField('Amount', validators=[validator.Optional(), validator.NumberRange(min=1)])
    percentage = form.FloatField('Percentage', validators=[validator.Optional(), validator.NumberRange(min=1, max=100)])
    is_active = form.BooleanField('Is Active', default=True)

    def validate(self):
        if not super(DiscountForm, self).validate():
            return False
        if self.amount.data and self.percentage.data:
            flash('Both amount and percentage cannot be set at the same time', 'error')
            return False
        if not self.amount.data and not self.percentage.data:
            flash('Please provide either an amount or a percentage', 'error')
            return False
        return True


class ArticleForm(FlaskForm):
    title = form.StringField('Title', validators=[validator.DataRequired(), validator.Length(max=100)])
    summary = form.TextAreaField('Summary', validators=[validator.DataRequired()])
    content = form.TextAreaField('Content', validators=[validator.DataRequired()])
    # tags = form.SelectMultipleField('Tags', validators=[validator.Optional()], choices=[(1, 1), (2,2)])
    image = form.FileField('Image', validators=[validator.Optional()])
    is_published = form.BooleanField('Is Active', default=True)


class RegistrationForm(FlaskForm):
    first_name = form.StringField('First Name', validators=[validator.DataRequired(), validator.Length(max=50)],
                                  render_kw={"placeholder": "First Name"})
    last_name = form.StringField('Last Name', validators=[validator.DataRequired(), validator.Length(max=50)],
                                 render_kw={"placeholder": "Last Name"})
    phone_number = form.StringField('Phone Number', validators=[validator.Length(max=50)],
                                    render_kw={"placeholder": "Phone Number"})
    email = form.StringField('Email', validators=[validator.DataRequired(), validator.Email(),
                                                  validator.Length(max=50)], render_kw={"placeholder": "Email Address"})
    password = form.PasswordField('Password', validators=[validator.DataRequired(), validator.Length(max=50),
                                                          validator.EqualTo('confirm_password',
                                                                            message="Passwords must match")],
                                  render_kw={"placeholder": "Password"})
    confirm_password = form.PasswordField('Confirm Password', validators=[validator.DataRequired(),
                                                                          validator.Length(max=50)],
                                          render_kw={"placeholder": "Confirm Password"})
    terms_and_conditions = form.BooleanField(validators=[validator.DataRequired()])


class LoginForm(FlaskForm):
    email = form.StringField('Email', validators=[validator.DataRequired(), validator.Email(),
                                                  validator.Length(max=50)], render_kw={"placeholder": "Email Address"})
    password = form.PasswordField('Password', validators=[validator.DataRequired(), validator.Length(max=50)],
                                  render_kw={"placeholder": "Password"})
    remember_me = form.BooleanField('Remember Me', default=True)


class VerificationForm(FlaskForm):
    email = form.StringField('Email', validators=[validator.DataRequired(), validator.Email(),
                                                  validator.Length(max=50)], render_kw={"placeholder": "Email Address"})
    verification_code = form.StringField('Verification Code', validators=[validator.DataRequired()],
                                         render_kw={"placeholder": "Verification Code"})


class RegistryForm(FlaskForm):
    name = form.StringField('Registry Name', validators=[validator.DataRequired(), validator.Length(max=100)],
                            render_kw={"placeholder": "Registry Name e.g Seyi & Funke's Wedding"})
    registry_type_id = form.SelectField('Event Type', coerce=int, validators=[validator.DataRequired()],
                                        render_kw={"placeholder": "Registry Type"})
    hashtag = form.StringField('Hashtag', validators=[validator.Optional()],
                               render_kw={"placeholder": "Event hashtag e.g #SeyFun20"})
    description = form.TextAreaField('Description', validators=[validator.DataRequired()],
                                     render_kw={"placeholder": "Registry Description"})
    image = form.FileField('Image', validators=[validator.Optional()])
    amount = form.FloatField('Target Amount', validators=[validator.Optional()],
                             render_kw={"placeholder": "Target Amount"})
    message = form.TextAreaField('Message', validators=[validator.Optional()],
                                 render_kw={"placeholder": "Message to people donating to your fund", 'style': "height: 200px;"})

    def validate(self):
        if not super(RegistryForm, self).validate():
            return False
        if self.amount.data and not self.message.data:
            flash('Please provide a message for your sponsors', 'error')
            return False
        return True


class RegistryProductForm(FlaskForm):
    name = form.StringField('Your Name', validators=[validator.DataRequired(), validator.Length(max=100)], render_kw={"placeholder": "Your Name"})
    phone_number = form.StringField('Your Phone Number', validators=[validator.DataRequired()], render_kw={"placeholder": "Your Phone Number"})
    address = form.TextAreaField('Delivery Address', validators=[validator.DataRequired()], render_kw={"placeholder": "Your Delivery Address"})
    city = form.StringField('Your City', validators=[validator.DataRequired()], render_kw={'placeholder': "Your City"})
    state = form.StringField('Your State', validators=[validator.DataRequired()], render_kw={'placeholder': "Your State"})
    products = form.SelectMultipleField('Products', coerce=int, validators=[validator.DataRequired(message="Please select at least one product")])


class AdminRegistryForm(FlaskForm):
    pass


class AddCartDiscount(FlaskForm):
    code = form.StringField('Discount code', validators=[validator.DataRequired()], render_kw={'placeholder': "Enter Your Code Here"})


class OrderForm(FlaskForm):
    first_name = form.StringField('First Name', validators=[validator.DataRequired(), validator.Length(max=100)])
    last_name = form.StringField('Last Name', validators=[validator.DataRequired(), validator.Length(max=100)])
    phone_number = form.StringField('Phone Number', validators=[validator.Length(max=50)])
    email = form.StringField('Email Address', validators=[validator.DataRequired(), validator.Email(), validator.Length(max=50)])
    message = form.TextAreaField('Message', validators=[validator.Optional()],
                                 render_kw={"placeholder": "Send a message to the celebrants"})


class DonationForm(FlaskForm):
    first_name = form.StringField('First Name', validators=[validator.DataRequired(), validator.Length(max=100)], render_kw={"placeholder": "Your First Name"})
    last_name = form.StringField('Last Name', validators=[validator.DataRequired(), validator.Length(max=100)], render_kw={"placeholder": "Your Last Name"})
    phone_number = form.StringField('Phone Number', validators=[validator.Length(max=50)], render_kw={"placeholder": "Your Phone Number"})
    email = form.StringField('Email Address', render_kw={"placeholder": "Your Email Address"},
                             validators=[validator.DataRequired(), validator.Email(), validator.Length(max=50)])
    amount = form.FloatField('Enter Amount', validators=[validator.DataRequired(), validator.NumberRange(min=0)],
                             render_kw={"placeholder": "Enter an Amount"})
    message = form.TextAreaField('Message', validators=[validator.Optional()],
                                 render_kw={"placeholder": "Send a message to the celebrants"})


class DeliveryForm(ModelForm):
    class Meta:
        model = RegistryDeliveryAddress

    registry_id = form.StringField(validators=[validator.Optional()])


class WeddingRegistryForm(ModelForm):
    class Meta:
        model = WeddingRegistry

    email = form.StringField(validators=[validator.Optional(), validator.Email(), validator.Length(max=50)], render_kw={"placeholder": "Email address"})
    month = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=MONTH_CHOICES)
    date = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=DATE_CHOICES)
    year = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=YEAR_CHOICES)
    address = ModelFormField(DeliveryForm)


class BabyShowerForm(ModelForm):
    class Meta:
        model = BabyShowerRegistry

    month = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=MONTH_CHOICES)
    date = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=DATE_CHOICES)
    year = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=YEAR_CHOICES)
    address = ModelFormField(DeliveryForm)


class BridalShowerForm(ModelForm):
    class Meta:
        model = BridalShowerRegistry

    month = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=MONTH_CHOICES)
    date = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=DATE_CHOICES)
    year = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=YEAR_CHOICES)
    address = ModelFormField(DeliveryForm)


class BirthdayForm(ModelForm):
    class Meta:
        model = BirthdayRegistry

    month = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=MONTH_CHOICES)
    date = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=DATE_CHOICES)
    year = form.SelectField(validators=[validator.DataRequired()], coerce=int, choices=YEAR_CHOICES)
    address = ModelFormField(DeliveryForm)

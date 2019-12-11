import wtforms as form
from wtforms import validators as validator
from flask import flash
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from flask_admin.form.widgets import Select2TagsWidget, Select2Widget
from models import Tag


class DiscountForm(form.Form):
    code = form.StringField('Code', validators=[validator.InputRequired(), validator.Length(max=50)])
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


class ArticleForm(form.Form):
    title = form.StringField('Title', validators=[validator.InputRequired(), validator.Length(max=100)])
    summary = form.TextAreaField('Summary', validators=[validator.InputRequired()])
    content = form.TextAreaField('Content', validators=[validator.InputRequired()])
    # tags = form.SelectMultipleField('Tags', validators=[validator.Optional()], choices=[(1, 1), (2,2)])
    image = form.FileField('Image', validators=[validator.Optional()])
    is_published = form.BooleanField('Is Active', default=True)


class RegistrationForm(form.Form):
    first_name = form.StringField('First Name', validators=[validator.InputRequired(), validator.Length(max=50)])
    last_name = form.StringField('Last Name', validators=[validator.InputRequired(), validator.Length(max=50)])
    email = form.StringField('Email', validators=[validator.InputRequired(), validator.Email(),
                                                  validator.Length(max=50)])
    password = form.PasswordField('Password', validators=[validator.InputRequired(), validator.Length(max=50),
                                                          validator.EqualTo('confirm_password',
                                                                            message="Passwords must match")])
    confirm_password = form.PasswordField('Confirm Password', validators=[validator.InputRequired(),
                                                                          validator.Length(max=50)])


class LoginForm(form.Form):
    email = form.StringField('Email', validators=[validator.InputRequired(), validator.Email(),
                                                  validator.Length(max=50)])
    password = form.PasswordField('Password', validators=[validator.InputRequired(), validator.Length(max=50)])
    remember_me = form.BooleanField('Remember Me', default=True)


class VerificationForm(form.Form):
    email = form.StringField('Email', validators=[validator.InputRequired(), validator.Email(),
                                                  validator.Length(max=50)])
    verification_code = form.StringField('Verification Code', validators=[validator.InputRequired()])

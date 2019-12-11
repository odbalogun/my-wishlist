from flask import redirect, render_template, url_for, Blueprint, flash, current_app, request
from forms import RegistrationForm, LoginForm, VerificationForm
from decorators import custom_login_required
from models import db, User
from flask_security.utils import hash_password, logout_user, login_user, verify_password

frontend = Blueprint('frontend', __name__, url_prefix='/')


@frontend.route('/')
def index():
    return render_template('frontend/index.html')


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        # check if user exists
        user = User.query.filter(email=form.email.data).first()
        if user:
            # check if password is correct
            if verify_password(form.password.data, user.password):
                if user.active:
                    # login user
                    login_user(user, remember=form.remember_me.data)
                    return redirect(url_for('.dashboard'))
                else:
                    if not user.has_verified_account:
                        flash('Please verify your account to proceed', 'error')
                    else:
                        flash('Your account is inactive. Please contact an administrator', 'error')
            else:
                flash('Email address and password do not match', 'error')
        else:
            flash('Your email address could not be found', 'error')
    return render_template('frontend/login.html', form=form)


@frontend.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate():
        # check that email does not exist already
        if bool(User.query.filter(email=form.email.data).first()):
            # create user
            user = User()
            form.populate_obj(user)
            user.password = hash_password(form.password.data)
            user.active = False
            user.generate_verification_code()
            db.session.add(user)
            db.session.commit()

            # todo send email with verification code
            return redirect(url_for('.verify', email=user.email, verification_code=user.verification_code))
        else:
            flash("Email address already exists", "error")
    return render_template('frontend/register.html', form=form)


@frontend.route('/verify/<email>/<verification_code>', methods=['GET', 'POST'])
def verify(email, verification_code):
    form = VerificationForm(data={'email': email, 'verification_code': verification_code})
    if request.method == 'POST' and form.validate():
        user = User.query.filter(email=form.email.data).first()

        if user:
            if user.verification_code == form.verification_code.data:
                user.active = True
                user.has_verified_account = True
                db.session.add(user)
                db.session.commit()

                login_user(user, remember=True)
                return redirect(url_for('.dashboard'))

        flash('Your email address and verification code do not match', 'error')
    return render_template('frontend/verification.html', form=form)


@frontend.route('/dashboard', methods=['GET', 'POST'])
@custom_login_required
def dashboard():
    pass


@frontend.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.index'))

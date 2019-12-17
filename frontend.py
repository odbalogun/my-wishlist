from flask import redirect, render_template, url_for, Blueprint, flash, request, abort
from forms import RegistrationForm, LoginForm, VerificationForm, RegistryForm, ManageProductForm
from decorators import custom_login_required
from models import db, User, Registry, Product, Article, Tag
from flask_security.utils import hash_password, logout_user, login_user, verify_password
from flask_security import current_user

frontend = Blueprint('frontend', __name__, url_prefix='/')


@frontend.route('/')
def index():
    return render_template('frontend/index.html')


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
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
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        # check that email does not exist already
        if not bool(User.query.filter_by(email=form.email.data).first()):
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
@frontend.route('/verify', methods=['GET', 'POST'])
def verify(email=None, verification_code=None):
    form = VerificationForm(request.form, data={'email': email, 'verification_code': verification_code})
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(email=form.email.data).first()

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
    return render_template('frontend/dashboard.html')


@frontend.route('/registry/my-registry', methods=['GET', 'POST'])
@custom_login_required
def my_registry():
    return render_template('frontend/my_registries.html')


@frontend.route('/registry/create-registry', methods=['GET', 'POST'])
@custom_login_required
def create_registry():
    form = RegistryForm(request.form)

    if request.method == 'POST' and form.validate():
        reg = Registry()
        reg.created_by = current_user
        form.populate_obj(reg)
        reg.generate_slug()
        reg.save()
        # todo save image
        flash("Please provide the following information", "success")
        return redirect(url_for('.add_products', slug=reg.slug))

    return render_template('frontend/create_registry.html', form=form)


@frontend.route('/registry/<slug>/manage-products', methods=['GET', 'POST'])
@custom_login_required
def manage_products(slug):
    # load registry
    registry = Registry.get_by_slug(slug)

    if not registry:
        abort(404)
    # ensure user can alter it
    if registry.created_by != current_user:
        abort(401)

    # get form
    products = Product.query.filter_by(is_available=True).all()
    form = ManageProductForm(request.form)
    form.products.choices = [(p.id, p.name) for p in products]
    return render_template('frontend/manage_products.html', registry=registry, products=products, form=form)


@frontend.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.index'))


@frontend.app_errorhandler(404)
def handle_404(e):
    return render_template('frontend/error.html', code=404, message="The page you're looking for could not be found")


@frontend.app_errorhandler(401)
def handle_401(e):
    return render_template('frontend/error.html', code=401, message="You are not authorized to view this page")


@frontend.route('/blog', methods=['GET'])
def blog():
    articles = Article.query.filter_by(is_published=True).all()
    tags = Tag.get_popular_tags(5)
    return render_template('frontend/blog.html', articles=articles, tags=tags)


@frontend.route('/blog/<slug>', methods=['GET'])
def blog_article(slug):
    article = Article.get_by_slug(slug)
    if not article:
        abort(404)
    recent_articles = Article.query.filter(Article.id != article.id).limit(5)
    tags = Tag.query.all()
    return render_template('frontend/blog_single.html', article=article, recent_articles=recent_articles, tags=tags)


@frontend.route('/frequently-asked-questions', methods=['GET'])
def faq():
    return render_template('frontend/about.html')


@frontend.route('/about-us', methods=['GET'])
def about():
    return render_template('frontend/about.html')


@frontend.route('/contact-us', methods=['GET', 'POST'])
def contact():
    return render_template('frontend/contact.html')

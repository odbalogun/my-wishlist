from flask import redirect, render_template, url_for, Blueprint, flash, request, abort, session
from forms import RegistrationForm, LoginForm, VerificationForm, RegistryForm, RegistryProductForm
from decorators import custom_login_required
from models import db, User, Registry, Product, Article, Tag, RegistryProducts, Category, HoneymoonFund, \
    RegistryDeliveryAddress
from flask_security.utils import hash_password, logout_user, login_user, verify_password
from flask_security import current_user
from utils import generate_full_file_path, generate_folder_name
from werkzeug.utils import secure_filename
import os

frontend = Blueprint('frontend', __name__, url_prefix='/')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@frontend.route('/')
def index():
    return render_template('frontend/index.html')


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data.lower()
        # check if user exists
        user = User.query.filter_by(email=email).first()
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


@frontend.route('/registry/create', methods=['GET', 'POST'])
@custom_login_required
def create_registry():
    form = RegistryForm(request.form)

    if request.method == 'POST' and form.validate():
        reg = Registry()
        reg.created_by = current_user
        form.populate_obj(reg)
        reg.generate_slug()

        image = request.files['image']
        if image:
            if allowed_file(image.filename):
                filename = secure_filename(image.filename)
                folder_name = generate_folder_name()

                image.save(generate_full_file_path('registries', folder_name, filename))

                reg.image = os.path.join('uploads', 'registries', folder_name, filename)
            else:
                flash('Please upload an image file', 'error')
                return redirect(url_for('.create_registry'))

        reg.save()
        if form.amount.data:
            db.session.add(HoneymoonFund(message=form.message.data, target_amount=form.amount.data,
                                         registry_id=reg.id))
            db.session.commit()

        flash("Please provide your delivery details and select products for your registry", "success")
        return redirect(url_for('.manage_products', slug=reg.slug))

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
    if registry.delivery:
        form = RegistryProductForm(request.form, obj=registry.delivery)
    else:
        form = RegistryProductForm(request.form, data={'name': current_user.full_name,
                                                               'phone_number': current_user.phone_number})
    form.products.choices = [(x.id, x.name) for x in products]
    categories = Category.query.all()

    if request.method == 'POST' and form.validate():
        delivery = RegistryDeliveryAddress.query.filter_by(registry_id=registry.id).first()

        if not delivery:
            delivery = RegistryDeliveryAddress(registry_id=registry.id)

        form.populate_obj(delivery)
        delivery.save()

        # populate products
        RegistryProducts.query.filter_by(registry_id=registry.id).delete()
        db.session.commit()
        product_list = []
        for item in form.products.data:
            product_list.append(RegistryProducts(product_id=item))
        registry.registry_products.extend(product_list)
        db.session.add(registry)
        db.session.commit()

        flash("Your registry has been successfully updated", "success")
        return redirect(url_for('.dashboard'))

    return render_template('frontend/manage_products.html', registry=registry, products=products, form=form, categories=categories)


@frontend.route('/registry/<slug>/add-product/<product_id>', methods=['GET'])
@custom_login_required
def add_product(slug, product_id):
    # load registry
    registry = Registry.get_by_slug(slug)
    product = Product.query.get(product_id)

    if not registry or not product:
        abort(404)

    if registry.created_by != current_user:
        abort(401)

    if product.id in registry.product_ids:
        flash("This product is already in your registry wishlist", "error")
        return redirect(url_for('.manage_products', slug=slug))

    registry.registry_products.append(RegistryProducts(product_id=product.id))
    db.session.add(registry)
    db.session.commit()

    flash("This product has been added to your registry wishlist", "success")
    return redirect(url_for('.manage_products', slug=slug))


@frontend.route('/registry/<slug>/remove-product/<product_id>', methods=['GET'])
@custom_login_required
def remove_product(slug, product_id):
    registry = Registry.get_by_slug(slug)
    product = Product.query.get(product_id)

    if not registry or not product:
        abort(404)

    if registry.created_by != current_user:
        abort(401)

    if product.id not in registry.product_ids:
        flash("This product is not in your registry wishlist", "error")
        return redirect(url_for('.manage_products', slug=slug))

    RegistryProducts.query.filter_by(product_id=product.id, registry_id=registry.id).delete()
    db.session.commit()

    flash("This product has been removed from your registry wishlist", "success")
    return redirect(url_for('.manage_products', slug=slug))


@frontend.route('/registry/<slug>/deactivate', methods=["GET"])
@custom_login_required
def deactivate_registry(slug):
    registry = Registry.get_by_slug(slug)

    if not registry:
        abort(404)

    if registry.created_by != current_user:
        abort(401)

    registry.is_active = False
    db.session.add(registry)
    db.session.commit()

    flash("Registry has been successfully deactivated", "success")
    return redirect(url_for('.dashboard'))


@frontend.route('/registry/<slug>/activate', methods=["GET"])
@custom_login_required
def activate_registry(slug):
    registry = Registry.get_by_slug(slug)

    if not registry:
        abort(404)

    if registry.created_by != current_user:
        abort(401)

    registry.is_active = True
    db.session.add(registry)
    db.session.commit()

    flash("Registry has been successfully activated", "success")
    return redirect(url_for('.dashboard'))


@frontend.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.index'))


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


@frontend.route('/registries', methods=['GET'])
def registries():
    registries = Registry.query.filter_by(is_active=True).all()
    return render_template('frontend/registries.html', registries=registries)


@frontend.route('/registries/<slug>', methods=['GET', 'POST'])
def view_registry(slug):
    registry = Registry.get_by_slug(slug)

    if not registry:
        abort(404)

    return render_template('frontend/registry.html', registry=registry)


@frontend.route('/products/<slug>', methods=['GET'])
def product_details(slug):
    product = Product.get_by_slug(slug)
    if not product:
        abort(404)
    return render_template('frontend/product_details.html', product=product)


@frontend.route('/frequently-asked-questions', methods=['GET'])
def faq():
    return render_template('frontend/about.html')


@frontend.route('/about-us', methods=['GET'])
def about():
    return render_template('frontend/about.html')


@frontend.route('/contact-us', methods=['GET', 'POST'])
def contact():
    return render_template('frontend/contact.html')


@frontend.app_errorhandler(404)
def handle_404(e):
    return render_template('frontend/error.html', code=404, message="The page you're looking for could not be found")


@frontend.app_errorhandler(401)
def handle_401(e):
    return render_template('frontend/error.html', code=401, message="You are not authorized to view this page")


@frontend.app_errorhandler(500)
def handle_500(e):
    return render_template('frontend/error.html', code=500, message="There has been an error. Please contact an administrator")


@frontend.route('/cart', methods=['GET'])
def cart():
    if 'cart_item' not in session:
        flash("There are no items in your cart yet", "error")
        return redirect(url_for('.registries'))
    products = RegistryProducts.query.filter(RegistryProducts.id.in_(session['cart_item'].keys()))
    return render_template('frontend/cart.html', products=products)


@frontend.route('/cart/add-product/<product_id>', methods=['GET'])
def add_product_to_cart(product_id):
    _quantity = 1
    product = RegistryProducts.query.get(product_id)

    if not product:
        abort(404)

    if not product.product.is_available:
        flash("This product is currently out of stock", "error")
        return redirect(url_for('.registries'))

    all_total_price = 0
    all_total_quantity = 0
    session.modified = True

    if 'cart_item' in session:
        if product_id in session['cart_item']:
            for key, value in session['cart_item'].items():
                if product_id == key:
                    old_quantity = session['cart_item'][key]['quantity']
                    total_quantity = old_quantity + _quantity
                    session['cart_item'][key]['quantity'] = total_quantity
                    session['cart_item'][key]['total_price'] = total_quantity * product.product.price
        else:
            session['cart_item'][product_id] = {'quantity': _quantity,
                                                'total_price': _quantity * product.product.price}
    else:
        session['cart_item'] = {product_id: {'quantity': _quantity, 'total_price': _quantity * product.product.price}}

    for key, value in session['cart_item'].items():
        individual_quantity = int(session['cart_item'][key]['quantity'])
        individual_price = float(session['cart_item'][key]['total_price'])
        all_total_quantity = all_total_quantity + individual_quantity
        all_total_price = all_total_price + individual_price

    session['all_total_quantity'] = all_total_quantity
    session['all_total_price'] = all_total_price

    flash('Your cart has been updated', 'success')
    return redirect(url_for('.view_registry', slug=product.registry.slug))


@frontend.route('/cart/empty', methods=['GET'])
def empty_cart():
    try:
        session.clear()
        return redirect(url_for('.registries'))
    except Exception as e:
        print(e)


@frontend.route('/cart/delete/<string:product_id>', methods=['GET'])
def delete_product(product_id):
    try:
        all_total_price = 0
        all_total_quantity = 0
        session.modified = True

        for item in session['cart_item'].items():
            if item[0] == product_id:
                session['cart_item'].pop(item[0], None)
                if 'cart_item' in session:
                    for key, value in session['cart_item'].items():
                        individual_quantity = int(session['cart_item'][key]['quantity'])
                        individual_price = float(session['cart_item'][key]['total_price'])
                        all_total_quantity = all_total_quantity + individual_quantity
                        all_total_price = all_total_price + individual_price
                break

        if all_total_quantity == 0:
            session.clear()
        else:
            session['all_total_quantity'] = all_total_quantity
            session['all_total_price'] = all_total_price

        # return redirect('/')
        return redirect(url_for('.cart'))
    except Exception as e:
        print(e)

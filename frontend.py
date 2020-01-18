from flask import redirect, render_template, url_for, Blueprint, flash, request, abort, session, jsonify
from forms import RegistrationForm, LoginForm, VerificationForm, RegistryForm, RegistryProductForm, AddCartDiscount, \
    OrderForm, NewsletterForm, DonationForm
from decorators import custom_login_required
from models import db, User, Registry, Product, Article, Tag, RegistryProducts, Category, HoneymoonFund, \
    RegistryDeliveryAddress, Discount, Order, OrderItem, Newsletter, Transaction, RegistryType, Donation
from flask_security.utils import hash_password, logout_user, login_user, verify_password
from flask_security import current_user
from utils import generate_full_file_path, generate_folder_name
from werkzeug.utils import secure_filename
from payment import PaystackPay
import os
import datetime

frontend = Blueprint('frontend', __name__, url_prefix='/')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@frontend.route('/')
@frontend.route('/index')
def index():
    form = NewsletterForm(request.form)

    return render_template('frontend/index.html', form=form)


@frontend.route('/registries/search', methods=['GET'])
def search():
    search_term = "%{}%".format(request.args.get('q'))
    registries = Registry.query.filter(Registry.name.like(search_term)).all()

    return render_template('frontend/search.html', registries=registries)


@frontend.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscription():
    form = NewsletterForm(request.form)

    if form.validate_on_submit():
        # check if email is unique
        email = Newsletter.query.filter_by(email=form.email.data).first()

        if not email:
            # save email
            email = Newsletter(email=form.email.data)
            email.save()
            flash("Thank you for subscribing to our newsletter", "success")
        else:
            flash("You are already subscribed to our newsletter", "error")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(f'{error}', "error")
                break
            break
    return redirect(url_for('.index'))


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
                        return redirect(url_for('.verify'))
                    else:
                        flash('Your account is inactive. Please contact an administrator', 'error')
            else:
                flash('Email address and password do not match', 'error')
        else:
            flash('Your email address could not be found', 'error')
    return render_template('frontend/login.html', form=form)


@frontend.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('.dashboard'))

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
    form.registry_type_id.choices = [(x.id, x.name) for x in RegistryType.get_active_records()]
    if request.method == 'POST' and form.validate():
        reg = Registry()
        reg.created_by = current_user
        form.populate_obj(reg)
        # check hashtag
        if reg.hashtag:
            if reg.hashtag[0] != '#':
                reg.hashtag = f'#{reg.hashtag}'
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

    if form.validate_on_submit():
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
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(f'{error}', "error")
                break
            break

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
    reg_list = Registry.query.filter_by(is_active=True)
    reg_type = request.args.get('type', None)

    if reg_type:
        category = RegistryType.get_by_slug(reg_type)
        if category:
            reg_list = reg_list.filter_by(registry_type_id=category.id)
    return render_template('frontend/registries.html', registries=reg_list.all())


@frontend.route('/registries/<slug>', methods=['GET', 'POST'])
def view_registry(slug):
    registry = Registry.get_by_slug(slug)
    if not registry:
        abort(404)

    form = DonationForm(request.form)
    if form.validate_on_submit():
        tran = Transaction()
        form.populate_obj(tran)
        tran.total_amount = form.amount.data
        tran.payment_status = 'unpaid'
        tran.type = 'donation'
        tran.save()

        tran.generate_txn_number()
        tran.save()

        donation = Donation()
        donation.registry_id = registry.id
        donation.transaction_id = tran.id
        donation.amount = form.amount.data
        donation.save()

        # initialize payments
        paystack = PaystackPay()
        response = paystack.fetch_authorization_url(email=tran.email, amount=tran.total_amount)

        if response.status_code == 200:
            json_response = response.json()

            tran.update(payment_txn_number=json_response['data']['reference'])
            return redirect(json_response['data']['authorization_url'])
        else:
            flash('Something went wrong. Please try again', 'error')

    return render_template('frontend/registry.html', registry=registry, form=form)


@frontend.route('/products/<slug>', methods=['GET'])
def product_details(slug):
    product = Product.get_by_slug(slug)
    if not product:
        abort(404)
    return render_template('frontend/product_details.html', product=product)


@frontend.route('/how-it-works', methods=['GET', 'POST'])
def faq():
    form = NewsletterForm(request.form)
    return render_template('frontend/how_it_works.html', form=form)


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
    return render_template('frontend/error.html', code=500,
                           message="There has been an error. Please contact an administrator")


@frontend.route('/cart', methods=['GET'])
def cart():
    if 'cart_item' not in session:
        flash("There are no items in your cart", "error")
        return redirect(url_for('.registries'))

    discount_form = AddCartDiscount()
    products = session['cart_item']
    return render_template('frontend/cart.html', products=products, discount_form=discount_form)


@frontend.route('/checkout', methods=['GET', 'POST'])
def checkout():
    form = OrderForm(request.form)
    if request.method == 'POST' and form.validate():
        tran = Transaction()
        form.populate_obj(tran)
        tran.type = 'order'
        tran.total_amount = session['all_total_price']
        tran.payment_status = 'unpaid'
        tran.save()

        tran.generate_txn_number()
        if 'discount_id' in session:
            tran.discount_id = session['discount_id']
            tran.discounted_amount = session['discounted_price']
        tran.save()

        # save order items
        for key, product in session['cart_item'].items():
            # check if there is an existing order
            order = Order.query.filter_by(transaction_id=tran.id, registry_id=product['registry']['id']).first()

            if not order:
                order = Order()
                order.registry_id = product['registry']['id']
                order.transaction_id = tran.id
                order.status = 'pending'
                order.save()

                order.generate_order_number()
                order.save()

            item = OrderItem(order_id=order.id, reg_product_id=key, quantity=product['quantity'],
                             unit_price=product['unit_price'],
                             total_price=product['total_price'])
            item.save()

        # initialize payments
        paystack = PaystackPay()
        amount = tran.discounted_amount if tran.discounted_amount else tran.total_amount
        response = paystack.fetch_authorization_url(email=tran.email, amount=amount)

        if response.status_code == 200:
            json_response = response.json()

            tran.update(payment_txn_number=json_response['data']['reference'])
            return redirect(json_response['data']['authorization_url'])
        else:
            flash('Something went wrong. Please try again', 'error')
            return redirect(url_for('.checkout'))

    products = session['cart_item']
    return render_template('frontend/checkout.html', form=form, products=products)


@frontend.route('/cart/verify-payment', methods=['GET', 'POST'])
def verify_payment():
    reference = request.args.get('reference')

    if not reference:
        flash('Payment failed. Please try again', 'error')
        return redirect(url_for('.registries'))

    # get order
    tran = Transaction.query.filter_by(payment_txn_number=reference).first()

    if not tran:
        flash('Something went wrong. Please contact an administrator', 'error')
        return redirect(url_for('.registries'))

    if tran.payment_status == 'paid':
        flash('Payment successful', 'success')
        return redirect(url_for('.registries'))

    paystack = PaystackPay()
    response = paystack.verify_reference_transaction(reference)

    if response.status_code == 200:
        tran.update(payment_status='paid', date_paid=datetime.datetime.now())
        # todo send emails to admin, customer, and purchaser
        flash('Your purchase has been completed', 'success')
    else:
        flash('The transaction could not be completed. Please try again', 'error')
    return redirect(url_for('.registries'))


@frontend.route('/cart/verify-payment-webhook', methods=['GET', 'POST'])
def verify_payment_webhook():
    reference = request.args.get('reference')

    if not reference:
        return jsonify({'error': 'No reference provided'}), 400

    # get order
    tran = Transaction.query.filter_by(payment_txn_number=reference).first()

    if not tran:
        return jsonify({'error': 'Reference code not found'}), 404

    if tran.payment_status == 'paid':
        return jsonify({'message': "Success"}), 200

    paystack = PaystackPay()
    response = paystack.verify_reference_transaction(reference)

    if response.status_code == 200:
        tran.update(payment_status='paid', date_paid=datetime.datetime.now())

        # todo send emails to admin, customer, and purchaser
        return jsonify({'message': "Your purchase has been completed"}), 200
    else:
        return jsonify({'error': "The transaction could not be verified"}), 400


@frontend.route('/add-cart-discount', methods=['POST'])
def add_cart_discount():
    discount_form = AddCartDiscount(request.form)

    if request.method == 'POST' and discount_form.validate():
        discount = Discount.query.filter_by(code=discount_form.code.data).first()

        if discount:
            if discount.is_active:
                # calculate discount
                discount_amount = discount.get_discount_amount(session['all_total_price'])
                session.modified = True
                # update cart
                session['discount_amount'] = discount_amount
                session['discounted_price'] = session['all_total_price'] - discount_amount
                session['discount_id'] = discount.id
                flash("Your discount has been successfully applied", 'success')
            else:
                flash("The discount code you entered has expired", 'error')
        else:
            flash("Invalid discount code provided", 'error')
    return redirect(url_for('.cart'))


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
                    session['cart_item'][key]['unit_price'] = product.product.price
                    session['cart_item'][key]['total_price'] = total_quantity * product.product.price
                    session['cart_item'][key]['product'] = product.product.to_json
                    session['cart_item'][key]['registry'] = product.registry.to_json
        else:
            session['cart_item'][product_id] = {'quantity': _quantity, 'unit_price': product.product.price,
                                                'product': product.product.to_json, 'registry': product.registry.to_json,
                                                'total_price': _quantity * product.product.price}
    else:
        session['cart_item'] = {product_id: {'quantity': _quantity, 'unit_price': product.product.price,
                                              'product': product.product.to_json, 'registry': product.registry.to_json,
                                              'total_price': _quantity * product.product.price}}

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

        flash("Your cart has been updated", 'success')
        return redirect(url_for('.cart'))
    except Exception as e:
        print(e)

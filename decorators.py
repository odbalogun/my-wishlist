from functools import wraps
from flask import current_app, request, redirect, url_for
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS


def custom_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return redirect(url_for('.login'))
        return func(*args, **kwargs)
    return decorated_view

from functools import wraps

from flask import abort, flash
from flask_login import current_user, login_required


def role_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in allowed_roles:
                flash("You do not have permission to access that page.", "danger")
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator

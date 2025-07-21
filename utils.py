# utils.py

from functools import wraps
from flask import abort
from flask_login import current_user

# Same hierarchy you had in app.py
ROLE_LEVEL = {
    'volunteer': 0,
    'reporter':  1,
    'admin':     2,
}

def role_required(min_role):
    """Abort with 403 unless current_user.role ≥ min_role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_role = getattr(current_user, 'role', None)
            if user_role is None or ROLE_LEVEL.get(user_role, 0) < ROLE_LEVEL[min_role]:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

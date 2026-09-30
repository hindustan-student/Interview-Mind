"""Auth helpers that still allow a static HTML export for Vercel."""

from functools import wraps

from flask import current_app
from flask_login import login_required


def login_required_unless_static(view):
    """Require login except when freezing a static academic demo."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_app.config.get("STATIC_EXPORT"):
            return view(*args, **kwargs)
        return login_required(view)(*args, **kwargs)

    return wrapped

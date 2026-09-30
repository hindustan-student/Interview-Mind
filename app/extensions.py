"""
InterviewMind - Flask Extensions
=================================
Single place to initialize Flask extensions so they can be shared
across modules without circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

# Database ORM
db = SQLAlchemy()

# User session management
login_manager = LoginManager()

# Password hashing
bcrypt = Bcrypt()

# CSRF protection for forms
csrf = CSRFProtect()

# Database migrations
migrate = Migrate()

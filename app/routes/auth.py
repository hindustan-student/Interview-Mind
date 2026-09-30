"""
InterviewMind - Authentication Routes Blueprint
================================================
Handles user registration, login, logout.
Uses Flask-Login for session management and Werkzeug for password hashing.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, bcrypt
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        full_name = (request.form.get("full_name") or "").strip()
        target_role = (request.form.get("target_role") or "").strip()

        # --- Server-side validation ---
        errors = _validate_registration(username, email, password, confirm)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "auth/register.html",
                form=request.form,
            )

        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            target_role=target_role or None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form={})


def _validate_registration(username, email, password, confirm):
    errors = []
    if len(username) < 3 or len(username) > 20:
        errors.append("Username must be 3-20 characters.")
    if not email or "@" not in email:
        errors.append("Please enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if User.query.filter_by(username=username).first():
        errors.append("Username already taken.")
    if User.query.filter_by(email=email).first():
        errors.append("Email already registered.")
    return errors


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            flash(f"Welcome back, {user.username}!", "success")
            next_url = request.args.get("next")
            # Safe redirect - only allow relative URLs
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=request.form if request.method == "POST" else {})


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))

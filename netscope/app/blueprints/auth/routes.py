from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.decorators import role_required
from app.extensions import db
from app.models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        if current_user.role == "staff":
            return redirect(url_for("staff.dashboard"))
        if current_user.role == "technician":
            return redirect(url_for("technician.dashboard"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        selected_role = (request.form.get("role") or "").strip()

        if selected_role not in {"admin", "staff", "technician"}:
            selected_role = None

        user = None
        if identifier:
            user = User.query.filter(
                (User.username == identifier) | (User.email == identifier.lower())
            ).first()

        if user is not None and user.check_password(password):
            if selected_role and user.role != selected_role:
                flash(f"This account is registered as a {user.role}. Please use the matching login option.", "danger")
                return render_template("auth/login.html", selected_role=selected_role)

            if not user.is_approved:
                flash("This account is pending approval by the super admin.", "warning")
                return render_template("auth/login.html", selected_role=selected_role or user.role)

            session.clear()
            login_user(user)
            flash("Login successful.", "success")
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            if user.role == "staff":
                return redirect(url_for("staff.dashboard"))
            return redirect(url_for("technician.dashboard"))

        flash("Invalid username/email or password.", "danger")
        return render_template("auth/login.html", selected_role=selected_role or "admin")

    return render_template("auth/login.html", selected_role="admin")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_route"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        requested_role = (request.form.get("role") or "staff").strip()

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if requested_role not in {"staff", "technician"}:
            flash("Admin accounts are managed by the super admin.", "danger")
            return render_template("auth/register.html")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("A user with that username or email already exists.", "danger")
            return render_template("auth/register.html")

        user = User(username=username, email=email, role=requested_role)
        user.is_approved = True
        user.is_super_admin = False
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

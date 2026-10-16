import os

import click
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_socketio import join_room
from flask_wtf.csrf import generate_csrf
from markupsafe import Markup
from sqlalchemy import inspect, text

from .extensions import csrf, db, login_manager, socketio
from .models import Asset, MaintenanceLog, Notification, Ticket, TicketMessage, User
from config import config


def _redirect_for_role(role):
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "staff":
        return redirect(url_for("staff.dashboard"))
    if role == "technician":
        return redirect(url_for("technician.dashboard"))
    return redirect(url_for("auth.login"))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config["default"])
    env_name = os.getenv("FLASK_ENV", "development").lower()
    app.config.from_object(config.get(env_name, config["default"]))

    if test_config:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.session_protection = "strong"
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    def ensure_user_approval_columns():
        with app.app_context():
            inspector = inspect(db.engine)
            if "users" not in inspector.get_table_names():
                db.create_all()
                return

            columns = {column["name"] for column in inspector.get_columns("users")}
            if "is_approved" not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN NOT NULL DEFAULT 1"))
            if "is_super_admin" not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN NOT NULL DEFAULT 0"))

            db.session.execute(text("UPDATE users SET is_approved = 1 WHERE role != 'admin' AND (is_approved IS NULL OR is_approved = 0)"))
            db.session.execute(text("UPDATE users SET is_super_admin = 1 WHERE id = (SELECT id FROM users WHERE role = 'admin' ORDER BY id ASC LIMIT 1)"))
            db.session.execute(text("UPDATE users SET is_approved = 1 WHERE role = 'admin' AND is_super_admin = 1"))
            db.session.commit()

    def ensure_ticket_resolution_columns():
        with app.app_context():
            inspector = inspect(db.engine)
            if "tickets" not in inspector.get_table_names():
                db.create_all()
                return

            columns = {column["name"] for column in inspector.get_columns("tickets")}
            for field_name, field_type in {
                "support_type": "VARCHAR(30)",
                "remote_support_id": "VARCHAR(120)",
                "resolution_method": "VARCHAR(30)",
                "diagnostic_steps": "TEXT",
                "actions_taken": "TEXT",
                "resolution_notes": "TEXT",
                "resolution_outcome": "VARCHAR(30)",
                "resolved_at": "DATETIME",
            }.items():
                if field_name not in columns:
                    db.session.execute(text(f"ALTER TABLE tickets ADD COLUMN {field_name} {field_type}"))
            db.session.commit()

    def ensure_asset_metadata_columns():
        with app.app_context():
            inspector = inspect(db.engine)
            if "assets" not in inspector.get_table_names():
                db.create_all()
                return

            columns = {column["name"] for column in inspector.get_columns("assets")}
            for field_name, field_type in {
                "brand": "VARCHAR(80)",
                "model": "VARCHAR(120)",
                "department": "VARCHAR(80)",
                "location": "VARCHAR(120)",
            }.items():
                if field_name not in columns:
                    db.session.execute(text(f"ALTER TABLE assets ADD COLUMN {field_name} {field_type}"))
            db.session.commit()

    def ensure_ticket_message_table():
        with app.app_context():
            inspector = inspect(db.engine)
            if "ticket_messages" not in inspector.get_table_names():
                db.create_all()
            db.session.commit()

    ensure_user_approval_columns()
    ensure_ticket_resolution_columns()
    ensure_asset_metadata_columns()
    ensure_ticket_message_table()

    def csrf_field():
        return generate_csrf()

    app.jinja_env.globals['csrf_token'] = csrf_field

    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf()}

    @app.context_processor
    def inject_tech_notifications():
        count = 0
        if current_user.is_authenticated and current_user.role == "technician":
            for ticket in Ticket.query.filter_by(technician_id=current_user.id).all():
                text = (ticket.title + " " + ticket.description).lower()
                if ticket.category in {"Hardware", "Network", "Access"} or "asset" in text or "device" in text or "computer" in text or "laptop" in text:
                    count += 1
        return {'tech_notification_count': count}

    @app.context_processor
    def inject_admin_notifications():
        if current_user.is_authenticated and current_user.role == "admin":
            notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.created_at.desc()).limit(8).all()
            unread_count = Notification.query.filter_by(recipient_id=current_user.id, is_read=False).count()
            return {'admin_notifications': notifications, 'admin_notification_count': unread_count}
        return {'admin_notifications': [], 'admin_notification_count': 0}


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @socketio.on("join_admin")
    def handle_join_admin(data):
        user_id = data.get("user_id") if isinstance(data, dict) else None
        if current_user.is_authenticated and current_user.id == int(user_id) and current_user.role == "admin":
            join_room(f"admin_{current_user.id}")

    @socketio.on("join_ticket_chat")
    def handle_join_ticket_chat(data):
        if not current_user.is_authenticated:
            return
        if not isinstance(data, dict):
            return
        ticket_id = data.get("ticket_id")
        if ticket_id is None:
            return
        ticket = Ticket.query.get(int(ticket_id))
        if not ticket:
            return
        is_allowed = ticket.created_by_id == current_user.id or ticket.technician_id == current_user.id
        if not is_allowed:
            return
        join_room(f"ticket_{ticket.id}")

    @socketio.on("send_ticket_message")
    def handle_send_ticket_message(data):
        if not current_user.is_authenticated:
            return
        if not isinstance(data, dict):
            return
        ticket_id = data.get("ticket_id")
        content = (data.get("content") or "").strip()
        if ticket_id is None or not content:
            return
        ticket = Ticket.query.get(int(ticket_id))
        if not ticket:
            return
        is_allowed = ticket.created_by_id == current_user.id or ticket.technician_id == current_user.id
        if not is_allowed:
            return
        if ticket.status in {"Resolved", "Closed"}:
            return
        message = TicketMessage(ticket_id=ticket.id, sender_id=current_user.id, content=content)
        db.session.add(message)
        db.session.commit()
        payload = {
            "id": message.id,
            "ticket_id": ticket.id,
            "sender_id": current_user.id,
            "sender_name": current_user.username,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
        socketio.emit("ticket_message_received", payload, room=f"ticket_{ticket.id}")

    @app.route("/tickets/<int:ticket_id>/messages", methods=["GET", "POST"])
    @login_required
    def ticket_messages(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        is_allowed = ticket.created_by_id == current_user.id or ticket.technician_id == current_user.id
        if not is_allowed:
            return render_template("errors/403.html"), 403

        if request.method == "POST":
            if ticket.status in {"Resolved", "Closed"}:
                return jsonify({"error": "This ticket is resolved and the chat is closed."}), 403

            payload = request.get_json(silent=True) or request.form
            content = (payload.get("content") or "").strip()
            if not content:
                return jsonify({"error": "Message cannot be empty."}), 400

            message = TicketMessage(ticket_id=ticket.id, sender_id=current_user.id, content=content)
            db.session.add(message)
            db.session.commit()
            event_payload = {
                "id": message.id,
                "ticket_id": ticket.id,
                "sender_id": current_user.id,
                "sender_name": current_user.username,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            socketio.emit("ticket_message_received", event_payload, room=f"ticket_{ticket.id}")
            return jsonify(event_payload), 201

        messages = TicketMessage.query.filter_by(ticket_id=ticket.id).order_by(TicketMessage.created_at.asc()).all()
        return jsonify([
            {
                "id": message.id,
                "ticket_id": ticket.id,
                "sender_id": message.sender_id,
                "sender_name": message.sender.username,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in messages
        ])

    from .blueprints.admin.routes import admin_bp
    from .blueprints.auth.routes import auth_bp
    from .blueprints.staff.routes import staff_bp
    from .blueprints.technician.routes import technician_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(technician_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return _redirect_for_role(current_user.role)
        return render_template("landing.html")

    @app.route("/dashboard")
    @login_required
    def dashboard_route():
        return _redirect_for_role(current_user.role)

    @app.cli.command("init-db")
    @click.option("--drop/--no-drop", default=False, help="Drop existing tables before recreating them.")
    def init_db(drop):
        if drop:
            db.drop_all()
        db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True, help="Administrator username")
    @click.option("--email", prompt=True, help="Administrator email")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Administrator password")
    def create_admin(username, email, password):
        username = username.strip()
        email = email.strip().lower()

        if User.query.filter((User.username == username) | (User.email == email)).first():
            raise click.ClickException("A user with that username or email already exists.")

        user = User(username=username, email=email, role="admin", is_approved=True, is_super_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Administrator '{username}' created successfully.")

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500

    return app

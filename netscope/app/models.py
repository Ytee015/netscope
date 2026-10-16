from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    is_approved = db.Column(db.Boolean, nullable=False, default=True)
    is_super_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    assigned_assets = db.relationship(
        "Asset",
        foreign_keys="Asset.assigned_to_id",
        back_populates="assigned_to",
        cascade="all, delete-orphan",
    )
    created_tickets = db.relationship(
        "Ticket",
        foreign_keys="Ticket.created_by_id",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    assigned_tickets = db.relationship(
        "Ticket",
        foreign_keys="Ticket.technician_id",
        back_populates="technician",
        cascade="all, delete-orphan",
    )
    maintenance_logs = db.relationship(
        "MaintenanceLog",
        foreign_keys="MaintenanceLog.technician_id",
        back_populates="technician",
        cascade="all, delete-orphan",
    )
    notifications = db.relationship(
        "Notification",
        foreign_keys="Notification.recipient_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Asset(db.Model):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("asset_tag", name="uq_assets_asset_tag"),
        UniqueConstraint("serial_number", name="uq_assets_serial_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(80), nullable=True)
    model = db.Column(db.String(120), nullable=True)
    serial_number = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="Available")
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_assets")
    maintenance_logs = db.relationship(
        "MaintenanceLog",
        foreign_keys="MaintenanceLog.asset_id",
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    status = db.Column(db.String(30), nullable=False, default="Open")
    category = db.Column(db.String(50), nullable=False)
    support_type = db.Column(db.String(30), nullable=True)
    remote_support_id = db.Column(db.String(120), nullable=True)
    resolution_method = db.Column(db.String(30), nullable=True)
    diagnostic_steps = db.Column(db.Text, nullable=True)
    actions_taken = db.Column(db.Text, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    resolution_outcome = db.Column(db.String(30), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    creator = db.relationship("User", foreign_keys=[created_by_id], back_populates="created_tickets")
    technician = db.relationship("User", foreign_keys=[technician_id], back_populates="assigned_tickets")
    notifications = db.relationship("Notification", back_populates="ticket", cascade="all, delete-orphan")
    messages = db.relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(db.Model):
    __tablename__ = "ticket_messages"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    ticket = db.relationship("Ticket", back_populates="messages")
    sender = db.relationship("User", foreign_keys=[sender_id])


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    recipient = db.relationship("User", foreign_keys=[recipient_id], back_populates="notifications")
    ticket = db.relationship("Ticket", back_populates="notifications")


class MaintenanceLog(db.Model):
    __tablename__ = "maintenance_logs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, nullable=False, default=0.0)
    performed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    asset = db.relationship("Asset", foreign_keys=[asset_id], back_populates="maintenance_logs")
    technician = db.relationship("User", foreign_keys=[technician_id], back_populates="maintenance_logs")

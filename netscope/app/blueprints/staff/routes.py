from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.decorators import role_required
from app.extensions import db, socketio
from app.models import Asset, Notification, Ticket, TicketMessage, User

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@role_required("staff")
def dashboard():
    assigned_assets = Asset.query.filter_by(assigned_to_id=current_user.id).count()
    open_tickets = Ticket.query.filter_by(created_by_id=current_user.id, status="Open").count()
    in_progress_tickets = Ticket.query.filter_by(created_by_id=current_user.id, status="In Progress").count()
    resolved_tickets = Ticket.query.filter_by(created_by_id=current_user.id, status="Resolved").count()

    return render_template(
        "staff/dashboard.html",
        assigned_assets=assigned_assets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
    )


@staff_bp.route("/assets")
@role_required("staff")
def assets():
    assets_list = Asset.query.filter_by(assigned_to_id=current_user.id).order_by(Asset.created_at.desc()).all()
    return render_template("staff/assets.html", assets=assets_list)


@staff_bp.route("/tickets/new", methods=["GET", "POST"])
@role_required("staff")
def create_ticket():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        category = (request.form.get("category") or "").strip()
        priority = (request.form.get("priority") or "Medium").strip()
        support_type = (request.form.get("support_type") or "").strip()
        remote_support_id = (request.form.get("remote_support_id") or "").strip()
        if not title or not description or not category:
            flash("Title, description, and category are required.", "danger")
            return render_template("staff/create_ticket.html")

        if priority not in {"Low", "Medium", "High", "Urgent"}:
            flash("Invalid priority selected.", "danger")
            return render_template("staff/create_ticket.html")

        if category not in {"Hardware", "Software", "Network", "Access"}:
            flash("Invalid category selected.", "danger")
            return render_template("staff/create_ticket.html")

        if support_type and support_type not in {"On-site", "Remote"}:
            flash("Invalid support type selected.", "danger")
            return render_template("staff/create_ticket.html")

        if support_type == "Remote":
            if not remote_support_id:
                flash("Please provide the AnyDesk ID for remote support requests.", "danger")
                return render_template("staff/create_ticket.html")
        else:
            remote_support_id = None

        ticket = Ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            support_type=support_type or None,
            remote_support_id=remote_support_id or None,
            status="Open",
            created_by_id=current_user.id,
            technician_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(ticket)
        db.session.commit()

        admins = User.query.filter_by(role="admin").all()
        created_notifications = []
        for admin in admins:
            notification = Notification(
                recipient_id=admin.id,
                ticket_id=ticket.id,
                message=f"{current_user.username} submitted a {ticket.priority} {ticket.category} ticket",
                link=url_for("admin.ticket_detail", ticket_id=ticket.id),
                is_read=False,
            )
            db.session.add(notification)
            created_notifications.append((admin, notification))
        db.session.commit()

        for admin, notification in created_notifications:
            socketio.emit(
                "new_ticket_notification",
                {
                    "id": notification.id,
                    "message": notification.message,
                    "link": notification.link,
                    "ticket_id": ticket.id,
                    "priority": ticket.priority,
                    "creator": current_user.username,
                },
                room=f"admin_{admin.id}",
            )

        asset_related = (
            category in {"Hardware", "Access", "Network"}
            or "asset" in title.lower()
            or "computer" in description.lower()
            or "device" in description.lower()
        )
        if asset_related:
            flash("Asset complaint reported. The IT support team has been notified.", "warning")
        else:
            flash("Ticket created successfully.", "success")
        return redirect(url_for("staff.tickets"))

    return render_template("staff/create_ticket.html")


@staff_bp.route("/tickets")
@role_required("staff")
def tickets():
    tickets_list = Ticket.query.filter_by(created_by_id=current_user.id).order_by(Ticket.updated_at.desc()).all()
    ticket_messages_by_ticket = {}
    for ticket in tickets_list:
        ticket_messages_by_ticket[ticket.id] = ticket.messages[-3:] if ticket.messages else []
    return render_template("staff/tickets.html", tickets=tickets_list, ticket_messages_by_ticket=ticket_messages_by_ticket)


@staff_bp.route("/tickets/<int:ticket_id>")
@role_required("staff")
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.created_by_id != current_user.id:
        return render_template("errors/403.html"), 403
    ticket_messages = TicketMessage.query.filter_by(ticket_id=ticket.id).order_by(TicketMessage.created_at.asc()).all()
    return render_template("staff/ticket_details.html", ticket=ticket, ticket_messages=ticket_messages)

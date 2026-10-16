from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.decorators import role_required
from app.extensions import db
from app.models import Asset, MaintenanceLog, Ticket, TicketMessage

technician_bp = Blueprint("technician", __name__, url_prefix="/technician")


@technician_bp.route("/dashboard")
@role_required("technician")
def dashboard():
    assigned_tickets = Ticket.query.filter_by(technician_id=current_user.id).count()
    open_tickets = Ticket.query.filter_by(technician_id=current_user.id, status="Open").count()
    in_progress_tickets = Ticket.query.filter_by(technician_id=current_user.id, status="In Progress").count()
    resolved_tickets = Ticket.query.filter_by(technician_id=current_user.id, status="Resolved").count()
    assigned_ticket_list = Ticket.query.filter_by(technician_id=current_user.id).order_by(Ticket.updated_at.desc()).all()

    notifications = []
    for ticket in assigned_ticket_list:
        text = (ticket.title + " " + ticket.description).lower()
        if ticket.category in {"Hardware", "Network", "Access"} or "asset" in text or "device" in text or "computer" in text or "laptop" in text:
            notifications.append({
                "title": ticket.title,
                "status": ticket.status,
                "priority": ticket.priority,
                "message": "Asset complaint reported. The IT support team has been notified.",
                "ticket_id": ticket.id,
            })

    if notifications:
        if len(notifications) == 1:
            flash(f"{notifications[0]['title']}: Asset complaint reported. The IT support team has been notified.", "warning")
        else:
            flash(f"{len(notifications)} asset complaints require attention.", "warning")

    return render_template(
        "technician/dashboard.html",
        assigned_tickets=assigned_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        notifications=notifications,
        assigned_tickets_list=assigned_ticket_list,
    )


@technician_bp.route("/queue")
@role_required("technician")
def queue():
    tickets_list = Ticket.query.filter_by(technician_id=current_user.id).order_by(Ticket.updated_at.desc()).all()
    ticket_messages_by_ticket = {}
    for ticket in tickets_list:
        ticket_messages_by_ticket[ticket.id] = ticket.messages[-3:] if ticket.messages else []
    return render_template("technician/queue.html", tickets=tickets_list, ticket_messages_by_ticket=ticket_messages_by_ticket)


@technician_bp.route("/tickets/<int:ticket_id>")
@role_required("technician")
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.technician_id != current_user.id and current_user.role != "admin":
        return render_template("errors/403.html"), 403
    ticket_messages = TicketMessage.query.filter_by(ticket_id=ticket.id).order_by(TicketMessage.created_at.asc()).all()
    return render_template("technician/ticket_details.html", ticket=ticket, ticket_messages=ticket_messages)


@technician_bp.route("/tickets/<int:ticket_id>/start-work", methods=["POST"])
@role_required("technician")
def start_ticket_work(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.technician_id != current_user.id and current_user.role != "admin":
        return render_template("errors/403.html"), 403

    if ticket.status == "Open":
        ticket.status = "In Progress"
        ticket.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Work started. Ticket status changed to In Progress.", "success")
    else:
        flash("This ticket is already in progress or resolved.", "info")
    return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))


@technician_bp.route("/tickets/<int:ticket_id>/status", methods=["POST"])
@role_required("technician")
def update_ticket_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.technician_id != current_user.id and current_user.role != "admin":
        return render_template("errors/403.html"), 403

    new_status = request.form.get("status")
    resolution_method = (request.form.get("resolution_method") or "").strip()
    diagnostic_steps = (request.form.get("diagnostic_steps") or "").strip()
    actions_taken = (request.form.get("actions_taken") or "").strip()
    resolution_notes = (request.form.get("resolution_notes") or "").strip()
    resolution_outcome = (request.form.get("resolution_outcome") or "").strip()

    if resolution_method in {"Remote Support", "On-site Support"}:
        ticket.resolution_method = resolution_method
    elif resolution_method:
        flash("Invalid resolution method selected.", "danger")
        return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))

    if diagnostic_steps:
        ticket.diagnostic_steps = diagnostic_steps
    if actions_taken:
        ticket.actions_taken = actions_taken
    if resolution_notes:
        ticket.resolution_notes = resolution_notes
    valid_outcomes = {"Resolved", "Unable to Resolve"}
    if resolution_outcome in valid_outcomes:
        ticket.resolution_outcome = resolution_outcome
    elif resolution_outcome:
        flash("Invalid resolution outcome selected.", "danger")
        return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))

    valid_transitions = {
        "Open": "In Progress",
        "In Progress": "Resolved",
    }

    if new_status not in {"In Progress", "Resolved"}:
        flash("Invalid ticket status transition.", "danger")
        return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))

    if ticket.status == new_status:
        flash("This ticket is already in the selected status.", "info")
        return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))

    if ticket.status in valid_transitions:
        if valid_transitions[ticket.status] != new_status:
            flash("Invalid ticket status transition.", "danger")
            return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))
    elif ticket.status in {"Resolved", "Closed"}:
        flash("Invalid ticket status transition.", "danger")
        return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))
    else:
        flash("This ticket is not in a status that can be updated by a technician.", "danger")
        return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))

    if new_status == "Resolved":
        if resolution_outcome == "Unable to Resolve":
            flash("Unable to resolve. The ticket must remain in progress.", "warning")
            ticket.status = "In Progress"
            ticket.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))
        if not ticket.resolution_notes or len(ticket.resolution_notes.strip()) < 10:
            flash("Meaningful resolution notes are required before a ticket can be marked Resolved.", "danger")
            return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))

    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)
    if new_status == "Resolved":
        ticket.resolved_at = datetime.now(timezone.utc)
    else:
        ticket.resolved_at = None
    db.session.commit()
    flash("Ticket status updated successfully.", "success")
    return redirect(url_for("technician.ticket_detail", ticket_id=ticket.id))


@technician_bp.route("/maintenance", methods=["GET", "POST"])
@role_required("technician")
def maintenance():
    assets = Asset.query.order_by(Asset.name.asc()).all()
    logs = MaintenanceLog.query.filter_by(technician_id=current_user.id).order_by(MaintenanceLog.performed_at.desc()).all()

    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        description = (request.form.get("description") or "").strip()
        cost_value = request.form.get("cost") or "0.0"

        if not asset_id:
            flash("An asset must be selected.", "danger")
            return render_template("technician/log_maintenance.html", assets=assets, logs=logs)

        asset = Asset.query.get(int(asset_id))
        if asset is None:
            flash("Selected asset does not exist.", "danger")
            return render_template("technician/log_maintenance.html", assets=assets, logs=logs)

        if not description:
            flash("Maintenance description is required.", "danger")
            return render_template("technician/log_maintenance.html", assets=assets, logs=logs)

        try:
            cost = float(cost_value)
        except (TypeError, ValueError):
            flash("Cost must be a numeric value.", "danger")
            return render_template("technician/log_maintenance.html", assets=assets, logs=logs)

        if cost < 0:
            flash("Cost cannot be negative.", "danger")
            return render_template("technician/log_maintenance.html", assets=assets, logs=logs)

        log = MaintenanceLog(
            asset_id=asset.id,
            technician_id=current_user.id,
            description=description,
            cost=cost,
            performed_at=datetime.now(timezone.utc),
        )
        db.session.add(log)
        db.session.commit()
        flash("Maintenance record saved successfully.", "success")
        return redirect(url_for("technician.maintenance"))

    return render_template("technician/log_maintenance.html", assets=assets, logs=logs)

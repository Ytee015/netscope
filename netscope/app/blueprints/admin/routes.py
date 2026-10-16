from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func

from app.decorators import role_required
from app.extensions import db
from app.models import Asset, MaintenanceLog, Notification, Ticket, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    total_assets = Asset.query.count()
    total_users = User.query.count()
    open_tickets = Ticket.query.filter_by(status="Open").count()
    resolved_tickets = Ticket.query.filter_by(status="Resolved").count()
    status_counts = {
        "Open": Ticket.query.filter_by(status="Open").count(),
        "In Progress": Ticket.query.filter_by(status="In Progress").count(),
        "Resolved": Ticket.query.filter_by(status="Resolved").count(),
        "Closed": Ticket.query.filter_by(status="Closed").count(),
    }

    technicians = User.query.filter_by(role="technician").all()
    pending_tickets = Ticket.query.filter(Ticket.status.in_(["Open", "In Progress"])).order_by(Ticket.updated_at.desc()).limit(6).all()

    monthly_labels = []
    monthly_values = []
    now = datetime.now(timezone.utc)
    for offset in range(5, -1, -1):
        month_index = (now.month - offset - 1) % 12 + 1
        year = now.year + ((now.month - offset - 1) // 12)
        label = datetime(year, month_index, 1).strftime("%b")
        monthly_labels.append(label)
        monthly_values.append(
            Ticket.query.filter(func.strftime("%Y-%m", Ticket.created_at) == f"{year}-{month_index:02d}").count()
        )

    asset_status_counts = [
        {"label": "Available", "count": Asset.query.filter_by(status="Available").count()},
        {"label": "Assigned", "count": Asset.query.filter_by(status="Assigned").count()},
        {"label": "Maintenance", "count": Asset.query.filter_by(status="Maintenance").count()},
        {"label": "Retired", "count": Asset.query.filter_by(status="Retired").count()},
    ]

    return render_template(
        "admin/dashboard.html",
        total_assets=total_assets,
        total_users=total_users,
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        status_counts=status_counts,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        asset_status_counts=asset_status_counts,
        pending_tickets=pending_tickets,
        technicians=technicians,
    )


@admin_bp.route("/notifications/read", methods=["POST"])
@role_required("admin")
def mark_notifications_read():
    Notification.query.filter_by(recipient_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return "", 204


@admin_bp.route("/assets")
@role_required("admin")
def assets():
    assets_list = Asset.query.order_by(Asset.created_at.desc()).all()
    return render_template("admin/assets.html", assets=assets_list)


@admin_bp.route("/assets/new", methods=["GET", "POST"])
@role_required("admin")
def create_asset():
    if request.method == "POST":
        asset_tag = (request.form.get("asset_tag") or "").strip()
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        brand = (request.form.get("brand") or "").strip()
        model = (request.form.get("model") or "").strip()
        serial_number = (request.form.get("serial_number") or "").strip()
        department = (request.form.get("department") or "").strip()
        location = (request.form.get("location") or "").strip()
        status = (request.form.get("status") or "Available").strip()
        assigned_to_id = request.form.get("assigned_to_id")
        purchase_date_raw = request.form.get("purchase_date")
        purchase_date = None
        if purchase_date_raw:
            purchase_date = datetime.strptime(purchase_date_raw, "%Y-%m-%d").date()

        if not all([asset_tag, name, category, serial_number]):
            flash("All required asset fields must be provided.", "danger")
            return render_template("admin/asset_form.html", asset=None, users=User.query.filter_by(role="staff").all())

        if status not in {"Available", "Assigned", "Maintenance", "Retired"}:
            flash("Invalid asset status.", "danger")
            return render_template("admin/asset_form.html", asset=None, users=User.query.filter_by(role="staff").all())

        if Asset.query.filter((Asset.asset_tag == asset_tag) | (Asset.serial_number == serial_number)).first():
            flash("Asset tag or serial number already exists.", "danger")
            return render_template("admin/asset_form.html", asset=None, users=User.query.filter_by(role="staff").all())

        assigned_user = None
        if assigned_to_id:
            assigned_user = User.query.filter_by(id=int(assigned_to_id), role="staff").first()
            if assigned_user is None:
                flash("Assignments must reference a valid staff member.", "danger")
                return render_template("admin/asset_form.html", asset=None, users=User.query.filter_by(role="staff").all())
            if status == "Retired":
                flash("Retired assets cannot be assigned.", "danger")
                return render_template("admin/asset_form.html", asset=None, users=User.query.filter_by(role="staff").all())
            status = "Assigned"

        asset = Asset(
            asset_tag=asset_tag,
            name=name,
            category=category,
            brand=brand or None,
            model=model or None,
            serial_number=serial_number,
            department=department or None,
            location=location or None,
            status=status,
            assigned_to=assigned_user,
            purchase_date=purchase_date or None,
        )

        db.session.add(asset)
        db.session.commit()
        flash("Asset created successfully.", "success")
        return redirect(url_for("admin.assets"))

    return render_template("admin/asset_form.html", asset=None, users=User.query.filter_by(role="staff").all())


@admin_bp.route("/assets/<int:asset_id>")
@role_required("admin")
def asset_detail(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    logs = MaintenanceLog.query.filter_by(asset_id=asset.id).order_by(MaintenanceLog.performed_at.desc()).all()
    return render_template("admin/asset_details.html", asset=asset, logs=logs)


@admin_bp.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if request.method == "POST":
        asset.asset_tag = (request.form.get("asset_tag") or asset.asset_tag).strip()
        asset.name = (request.form.get("name") or asset.name).strip()
        asset.category = (request.form.get("category") or asset.category).strip()
        asset.brand = (request.form.get("brand") or "").strip() or None
        asset.model = (request.form.get("model") or "").strip() or None
        asset.serial_number = (request.form.get("serial_number") or asset.serial_number).strip()
        asset.department = (request.form.get("department") or "").strip() or None
        asset.location = (request.form.get("location") or "").strip() or None
        status = (request.form.get("status") or asset.status).strip()
        assigned_to_id = request.form.get("assigned_to_id")
        purchase_date_raw = request.form.get("purchase_date")
        purchase_date = None
        if purchase_date_raw:
            purchase_date = datetime.strptime(purchase_date_raw, "%Y-%m-%d").date()

        if status not in {"Available", "Assigned", "Maintenance", "Retired"}:
            flash("Invalid asset status.", "danger")
            return render_template("admin/asset_form.html", asset=asset, users=User.query.filter_by(role="staff").all())

        if assigned_to_id:
            user = User.query.filter_by(id=int(assigned_to_id), role="staff").first()
            if user is None:
                flash("Assignment must reference a valid staff member.", "danger")
                return render_template("admin/asset_form.html", asset=asset, users=User.query.filter_by(role="staff").all())
            if status == "Retired":
                flash("Retired assets cannot be assigned.", "danger")
                return render_template("admin/asset_form.html", asset=asset, users=User.query.filter_by(role="staff").all())
            asset.assigned_to = user
            asset.status = "Assigned"
        else:
            asset.assigned_to = None
            if asset.status not in {"Maintenance", "Retired"}:
                asset.status = "Available"

        asset.purchase_date = purchase_date
        db.session.commit()
        flash("Asset updated successfully.", "success")
        return redirect(url_for("admin.asset_detail", asset_id=asset.id))

    return render_template("admin/asset_form.html", asset=asset, users=User.query.filter_by(role="staff").all())


@admin_bp.route("/assets/<int:asset_id>/delete", methods=["POST"])
@role_required("admin")
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    flash("Asset deleted successfully.", "success")
    return redirect(url_for("admin.assets"))


@admin_bp.route("/assets/<int:asset_id>/assign", methods=["POST"])
@role_required("admin")
def assign_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    user_id = request.form.get("user_id")
    if not user_id:
        flash("Please select a staff member.", "danger")
        return redirect(url_for("admin.asset_detail", asset_id=asset.id))

    user = User.query.filter_by(id=int(user_id), role="staff").first()
    if user is None:
        flash("Invalid staff member selection.", "danger")
        return redirect(url_for("admin.asset_detail", asset_id=asset.id))
    if asset.status == "Retired":
        flash("Retired assets cannot be assigned.", "danger")
        return redirect(url_for("admin.asset_detail", asset_id=asset.id))

    asset.assigned_to = user
    asset.status = "Assigned"
    db.session.commit()
    flash("Asset assigned successfully.", "success")
    return redirect(url_for("admin.asset_detail", asset_id=asset.id))


@admin_bp.route("/assets/<int:asset_id>/unassign", methods=["POST"])
@role_required("admin")
def unassign_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    asset.assigned_to = None
    if asset.status not in {"Maintenance", "Retired"}:
        asset.status = "Available"
    db.session.commit()
    flash("Asset unassigned successfully.", "success")
    return redirect(url_for("admin.asset_detail", asset_id=asset.id))


@admin_bp.route("/users")
@role_required("admin")
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users_list, can_manage_admins=current_user.is_super_admin)


@admin_bp.route("/users/<int:user_id>/approve", methods=["POST"])
@role_required("admin")
def approve_user(user_id):
    if not current_user.is_super_admin:
        flash("Only the super admin can approve pending accounts.", "danger")
        return redirect(url_for("admin.users"))

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f"User '{user.username}' has been approved.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/new", methods=["GET", "POST"])
@role_required("admin")
def create_user():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "staff").strip()

        allowed_roles = {"staff", "technician"}
        if current_user.is_super_admin:
            allowed_roles.add("admin")

        if role not in allowed_roles:
            flash("This role is not permitted for your account.", "danger")
            return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all(), can_manage_admins=current_user.is_super_admin)

        if not username or not email or not password:
            flash("Username, email, and password are required.", "danger")
            return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all(), can_manage_admins=current_user.is_super_admin)

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("A user with that username or email already exists.", "danger")
            return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all(), can_manage_admins=current_user.is_super_admin)

        user = User(username=username, email=email, role=role)
        user.is_approved = True
        user.is_super_admin = False
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("User account created successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all(), can_manage_admins=current_user.is_super_admin)


@admin_bp.route("/tickets")
@role_required("admin")
def tickets():
    query = Ticket.query
    status = request.args.get("status")
    priority = request.args.get("priority")
    category = request.args.get("category")
    technician_id = request.args.get("technician_id")

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)
    if technician_id:
        query = query.filter_by(technician_id=int(technician_id))

    tickets_list = query.order_by(Ticket.updated_at.desc()).all()
    technicians = User.query.filter_by(role="technician").all()
    return render_template("admin/tickets.html", tickets=tickets_list, technicians=technicians)


@admin_bp.route("/tickets/<int:ticket_id>")
@role_required("admin")
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template("admin/ticket_details.html", ticket=ticket)


@admin_bp.route("/tickets/<int:ticket_id>/assign", methods=["POST"])
@role_required("admin")
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    tech_id = request.form.get("technician_id")
    if not tech_id:
        flash("Please select a valid technician.", "danger")
        return redirect(url_for("admin.ticket_detail", ticket_id=ticket.id))

    technician = User.query.filter_by(id=int(tech_id), role="technician").first()
    if technician is None:
        flash("Selected user is not a registered technician.", "danger")
        return redirect(url_for("admin.ticket_detail", ticket_id=ticket.id))

    ticket.technician_id = technician.id
    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Ticket assigned successfully.", "success")
    return redirect(url_for("admin.ticket_detail", ticket_id=ticket.id))


@admin_bp.route("/tickets/<int:ticket_id>/status", methods=["POST"])
@role_required("admin")
def update_ticket_status_admin(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    new_status = request.form.get("status")
    if new_status not in {"Open", "In Progress", "Resolved", "Closed"}:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.ticket_detail", ticket_id=ticket.id))

    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Ticket status updated.", "success")
    return redirect(url_for("admin.ticket_detail", ticket_id=ticket.id))


@admin_bp.route("/reports")
@role_required("admin")
def reports():
    asset_status = []
    for label in ["Available", "Assigned", "Maintenance", "Retired"]:
        asset_status.append({"label": label, "count": Asset.query.filter_by(status=label).count()})

    ticket_status = []
    for label in ["Open", "In Progress", "Resolved", "Closed"]:
        ticket_status.append({"label": label, "count": Ticket.query.filter_by(status=label).count()})

    ticket_priorities = []
    for label in ["Low", "Medium", "High", "Urgent"]:
        ticket_priorities.append({"label": label, "count": Ticket.query.filter_by(priority=label).count()})

    ticket_categories = []
    for label in ["Hardware", "Software", "Network", "Access"]:
        ticket_categories.append({"label": label, "count": Ticket.query.filter_by(category=label).count()})

    workload = []
    for technician in User.query.filter_by(role="technician").all():
        workload.append({
            "name": technician.username,
            "count": Ticket.query.filter_by(technician_id=technician.id).count(),
        })

    maintenance_history = MaintenanceLog.query.order_by(MaintenanceLog.performed_at.desc()).all()
    return render_template(
        "admin/reports.html",
        asset_status=asset_status,
        ticket_status=ticket_status,
        ticket_priorities=ticket_priorities,
        ticket_categories=ticket_categories,
        workload=workload,
        maintenance_history=maintenance_history,
    )

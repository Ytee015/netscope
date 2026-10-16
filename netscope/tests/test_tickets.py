import pytest

from app import create_app
from app.extensions import db
from app.models import Asset, Ticket, User


@pytest.fixture()
def client():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def create_user(username, email, password, role):
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_staff_can_create_ticket_and_session_creator(client):
    staff = create_user("staffA", "staffA@example.com", "staffpass", "staff")
    with client:
        client.post("/auth/login", data={"identifier": "staffA", "password": "staffpass"})
        response = client.post(
            "/staff/tickets/new",
            data={
                "title": "Email issue",
                "description": "Cannot login to Outlook.",
                "category": "Access",
                "priority": "High",
                "support_type": "Remote",
                "remote_support_id": "456789123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        ticket = Ticket.query.filter_by(title="Email issue").first()
        assert ticket is not None
        assert ticket.created_by_id == staff.id
        assert ticket.support_type == "Remote"
        assert ticket.remote_support_id == "456789123"


def test_admin_can_assign_ticket_to_valid_technician(client):
    admin = create_user("adminA", "adminA@example.com", "adminpass", "admin")
    staff = create_user("staffB", "staffB@example.com", "staffpass", "staff")
    tech = create_user("techA", "techA@example.com", "techpass", "technician")
    ticket = Ticket(title="Wi-Fi", description="Slow network", category="Network", priority="Medium", status="Open", created_by_id=staff.id)
    db.session.add(ticket)
    db.session.commit()

    with client:
        client.post("/auth/login", data={"identifier": "adminA", "password": "adminpass"})
        response = client.post(f"/admin/tickets/{ticket.id}/assign", data={"technician_id": str(tech.id)}, follow_redirects=False)
        assert response.status_code == 302
        assert ticket.technician_id == tech.id


def test_technician_can_update_assigned_ticket(client):
    tech = create_user("techB", "techB@example.com", "techpass", "technician")
    staff = create_user("staffC", "staffC@example.com", "staffpass", "staff")
    ticket = Ticket(title="Laptop", description="Needs repair", category="Hardware", priority="High", status="Open", created_by_id=staff.id, technician_id=tech.id)
    db.session.add(ticket)
    db.session.commit()

    with client:
        client.post("/auth/login", data={"identifier": "techB", "password": "techpass"})
        response = client.post(f"/technician/tickets/{ticket.id}/status", data={"status": "In Progress"}, follow_redirects=False)
        assert response.status_code == 302
        assert Ticket.query.get(ticket.id).status == "In Progress"


def test_invalid_ticket_status_transitions_are_rejected(client):
    tech = create_user("techC", "techC@example.com", "techpass", "technician")
    staff = create_user("staffD", "staffD@example.com", "staffpass", "staff")
    ticket = Ticket(title="Server", description="Issue", category="Software", priority="Urgent", status="Resolved", created_by_id=staff.id, technician_id=tech.id)
    db.session.add(ticket)
    db.session.commit()

    with client:
        client.post("/auth/login", data={"identifier": "techC", "password": "techpass"})
        response = client.post(f"/technician/tickets/{ticket.id}/status", data={"status": "In Progress"}, follow_redirects=False)
        assert response.status_code == 302
        assert Ticket.query.get(ticket.id).status == "Resolved"


def test_technician_maintenance_log(client):
    tech = create_user("techD", "techD@example.com", "techpass", "technician")
    asset = Asset(asset_tag="AST-7001", name="Mouse", category="Hardware", serial_number="SN-7001", status="Available")
    db.session.add(asset)
    db.session.commit()

    with client:
        client.post("/auth/login", data={"identifier": "techD", "password": "techpass"})
        response = client.post(
            "/technician/maintenance",
            data={
                "asset_id": str(asset.id),
                "description": "Replaced batteries",
                "cost": "25.50",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302


def test_registration_accepts_staff_and_technician_only(client):
    for role in ["staff", "technician"]:
        username = f"{role}reg"
        email = f"{role}reg@example.com"
        response = client.post(
            "/auth/register",
            data={
                "username": username,
                "email": email,
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": role,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        user = User.query.filter_by(username=username).first()
        assert user is not None
        assert user.role == role

    response = client.post(
        "/auth/register",
        data={
            "username": "adminreg",
            "email": "adminreg@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "role": "admin",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert b"Admin accounts are managed by the super admin" in response.data

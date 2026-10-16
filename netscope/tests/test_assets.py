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


def test_admin_can_create_asset(client):
    admin = create_user("admin1", "admin1@example.com", "adminpass", "admin")
    with client:
        client.post("/auth/login", data={"identifier": "admin1", "password": "adminpass"})
        response = client.post(
            "/admin/assets/new",
            data={
                "asset_tag": "AST-1001",
                "name": "Laptop",
                "category": "Hardware",
                "serial_number": "SN-1001",
                "status": "Available",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert Asset.query.filter_by(asset_tag="AST-1001").count() == 1


def test_duplicate_asset_tags_are_rejected(client):
    admin = create_user("admin2", "admin2@example.com", "adminpass", "admin")
    with client:
        client.post("/auth/login", data={"identifier": "admin2", "password": "adminpass"})
        client.post(
            "/admin/assets/new",
            data={
                "asset_tag": "AST-1002",
                "name": "Laptop A",
                "category": "Hardware",
                "serial_number": "SN-1002",
                "status": "Available",
            },
            follow_redirects=False,
        )
        response = client.post(
            "/admin/assets/new",
            data={
                "asset_tag": "AST-1002",
                "name": "Laptop B",
                "category": "Hardware",
                "serial_number": "SN-1003",
                "status": "Available",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert Asset.query.filter_by(asset_tag="AST-1002").count() == 1


def test_staff_can_view_only_assigned_assets(client):
    admin = create_user("admin3", "admin3@example.com", "adminpass", "admin")
    staff = create_user("staff1", "staff1@example.com", "staffpass", "staff")
    staff2 = create_user("staff2", "staff2@example.com", "staffpass2", "staff")
    asset1 = Asset(asset_tag="AST-2001", name="Printer", category="Hardware", serial_number="SN-2001", status="Assigned", assigned_to=staff)
    asset2 = Asset(asset_tag="AST-2002", name="Monitor", category="Hardware", serial_number="SN-2002", status="Assigned", assigned_to=staff2)
    db.session.add_all([asset1, asset2])
    db.session.commit()
    with client:
        client.post("/auth/login", data={"identifier": "staff1", "password": "staffpass"})
        response = client.get("/staff/assets")
        assert response.status_code == 200
        assert b"Printer" in response.data
        assert b"Monitor" not in response.data


def test_unauthorized_asset_deletion_is_blocked(client):
    admin = create_user("admin4", "admin4@example.com", "adminpass", "admin")
    staff = create_user("staff3", "staff3@example.com", "staffpass", "staff")
    asset = Asset(asset_tag="AST-3001", name="Router", category="Network", serial_number="SN-3001", status="Available")
    db.session.add(asset)
    db.session.commit()
    with client:
        client.post("/auth/login", data={"identifier": "staff3", "password": "staffpass"})
        response = client.post(f"/admin/assets/{asset.id}/delete", follow_redirects=False)
        assert response.status_code == 403


def test_multiple_browser_profiles_keep_independent_sessions():
    admin_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })
    staff_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })

    with admin_app.app_context():
        db.create_all()
        create_user("admin5", "admin5@example.com", "adminpass", "admin")
        admin_client = admin_app.test_client()
        admin_login = admin_client.post("/auth/login", data={"identifier": "admin5", "password": "adminpass"}, follow_redirects=False)
        assert admin_login.status_code == 302
        admin_dashboard = admin_client.get("/admin/dashboard")
        assert admin_dashboard.status_code == 200
        assert b"Administrator dashboard" in admin_dashboard.data

    with staff_app.app_context():
        db.create_all()
        create_user("staff4", "staff4@example.com", "staffpass", "staff")
        staff_client = staff_app.test_client()
        staff_login = staff_client.post("/auth/login", data={"identifier": "staff4", "password": "staffpass"}, follow_redirects=False)
        assert staff_login.status_code == 302
        staff_dashboard = staff_client.get("/staff/dashboard")
        assert staff_dashboard.status_code == 200
        assert b"Staff dashboard" in staff_dashboard.data

        db.session.remove()
        db.drop_all()

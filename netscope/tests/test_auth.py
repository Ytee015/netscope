import pytest

from app import create_app
from app.extensions import db
from app.models import User


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


def test_successful_login(client):
    create_user("staff01", "staff01@example.com", "secret123", "staff")
    response = client.post("/auth/login", data={"identifier": "staff01", "password": "secret123"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/staff/dashboard")


def test_failed_login(client):
    create_user("staff02", "staff02@example.com", "secret123", "staff")
    response = client.post("/auth/login", data={"identifier": "staff02", "password": "wrongpass"}, follow_redirects=False)
    assert response.status_code == 200
    assert b"Invalid username/email or password" in response.data


def test_logout(client):
    create_user("staff03", "staff03@example.com", "secret123", "staff")
    with client:
        client.post("/auth/login", data={"identifier": "staff03", "password": "secret123"})
        response = client.post("/auth/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.location.endswith("/auth/login")


def test_password_hashing(client):
    user = create_user("staff04", "staff04@example.com", "secret123", "staff")
    assert user.password_hash != "secret123"
    assert user.check_password("secret123") is True


def test_public_registration_supports_staff_and_technician_only(client):
    for role in ["staff", "technician"]:
        username = f"{role}new"
        email = f"{role}new@example.com"
        response = client.post(
            "/auth/register",
            data={
                "username": username,
                "email": email,
                "password": "secret123",
                "confirm_password": "secret123",
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
            "username": "adminnew",
            "email": "adminnew@example.com",
            "password": "secret123",
            "confirm_password": "secret123",
            "role": "admin",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert b"Admin accounts are managed by the super admin" in response.data

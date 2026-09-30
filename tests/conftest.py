"""
InterviewMind - Test Suite Configuration
=========================================
Pytest fixtures that build an isolated test app + DB.
"""

import os
import sys
import tempfile
import pytest

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="function")
def app():
    """Create a fresh test app with an in-memory DB for each test."""
    from app import create_app
    from app.extensions import db

    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a registered test user and return (id, email, password)."""
    from app.extensions import db
    from app.models import User
    with app.app_context():
        user = User(username="testuser", email="test@example.com", full_name="Test User")
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "username": "testuser",
                "email": "test@example.com", "password": "testpassword123"}


@pytest.fixture
def logged_in_client(app, test_user):
    """A test client with the test_user already logged in."""
    client = app.test_client()
    client.post("/auth/login", data={
        "email": test_user["email"],
        "password": test_user["password"],
    }, follow_redirects=False)
    return client

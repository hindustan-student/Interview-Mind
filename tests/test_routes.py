"""
InterviewMind - Route Tests
============================
Smoke tests for all major routes.
"""

import os


def test_landing_page(client):
    """Landing page loads with the brand."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"InterviewMind" in response.data
    assert b"particle-canvas" in response.data  # neon particle canvas present


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About" in response.data


def test_features_page(client):
    response = client.get("/features")
    assert response.status_code == 200
    assert b"Mock Interview" in response.data


def test_contact_page(client):
    response = client.get("/contact")
    assert response.status_code == 200
    assert b"Contact" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "InterviewMind"


def test_login_page(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Welcome Back" in response.data


def test_register_page(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Create Your Free Account" in response.data


def test_dashboard_requires_auth(client):
    """Dashboard should redirect to login if not authenticated."""
    response = client.get("/dashboard/", follow_redirects=False)
    assert response.status_code in (301, 302)
    assert "/auth/login" in response.headers.get("Location", "")


def test_interview_start_requires_auth(client):
    response = client.get("/interview/start", follow_redirects=False)
    assert response.status_code in (301, 302)


def test_resume_upload_requires_auth(client):
    response = client.get("/resume/upload", follow_redirects=False)
    assert response.status_code in (301, 302)


def test_404_page(client):
    response = client.get("/nonexistent-page-xyz")
    assert response.status_code == 404


def test_register_and_login_flow(client, app):
    """End-to-end: register → login → access dashboard."""
    # Register
    response = client.post("/auth/register", data={
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "target_role": "Software Engineer",
        "password": "securepass123",
        "confirm_password": "securepass123",
    }, follow_redirects=False)
    assert response.status_code in (301, 302)
    assert "/auth/login" in response.headers.get("Location", "")

    # Login
    response = client.post("/auth/login", data={
        "email": "newuser@example.com",
        "password": "securepass123",
    }, follow_redirects=False)
    assert response.status_code in (301, 302)

    # Access dashboard
    response = client.get("/dashboard/", follow_redirects=False)
    assert response.status_code == 200


def test_question_bank_public(client):
    """Question bank is publicly browseable."""
    response = client.get("/questions/")
    assert response.status_code == 200
    assert b"Question Bank" in response.data

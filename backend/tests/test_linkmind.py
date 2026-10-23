import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db import Base, get_db
from app.core.ssrf import validate_safe_url
from app.core.security import create_access_token, hash_password
from app.models import User, UserProfile, Resource, Collection, Application, Resume, Source
from app.services.ai_adapter import heuristic_extract_opportunities, extract_skills_from_text
from app.services.matcher import calculate_recommendation

# Test SQLite in-memory database
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("secret123"),
        full_name="Tester"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = UserProfile(
        user_id=user.id,
        target_roles=["AI Engineer", "Software Engineer"],
        career_goals="Build scalable machine learning systems."
    )
    db_session.add(profile)
    db_session.commit()
    return user

@pytest.fixture
def user_token(test_user):
    return create_access_token(test_user.id)

# ----------------- TESTS -----------------

def test_empty_library_initial_state(client, user_token):
    """Verify library starts empty and dashboard shows real 0 counts (no fake data)"""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/api/v1/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["courses_saved"] == 0
    assert data["internships_saved"] == 0
    assert data["total_resources"] == 0

def test_ssrf_protection_blocks_restricted_destinations():
    """Verify SSRF blocks localhost, loopback, cloud metadata, and link-local"""
    unsafe_urls = [
        "http://localhost:8080/admin",
        "http://127.0.0.1:8000/secret",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0:80",
        "http://192.168.1.1/router",
        "http://10.0.0.1/internal",
        "ftp://example.com/file.txt",
    ]
    for url in unsafe_urls:
        is_safe, reason = validate_safe_url(url)
        assert not is_safe, f"URL '{url}' should have been blocked but passed! Reason: {reason}"

    # Public safe URL should pass
    is_safe, _ = validate_safe_url("https://www.google.com")
    assert is_safe

def test_one_source_many_opportunities_extraction():
    """Verify that a document/post containing multiple internships produces distinct separate records"""
    sample_multi_post = """
    Top Winter Tech Internships:
    
    1. Machine Learning Intern at Google
    Location: Remote
    Stipend: $50/hr
    Required Skills: Python, PyTorch, Scikit-learn
    Apply: https://careers.google.com/jobs/101
    Deadline: Nov 30, 2026
    
    2. Backend Developer Intern at Stripe
    Location: San Francisco, CA
    Compensation: $55/hr
    Required Skills: Go, Python, SQL, REST API
    Apply: https://stripe.com/jobs/intern-backend
    Deadline: Dec 15, 2026
    
    3. Data Analyst Intern at Netflix
    Location: Los Gatos, CA
    Required Skills: SQL, Python, Pandas
    Apply: https://jobs.netflix.com/data-intern
    """
    opportunities = heuristic_extract_opportunities(sample_multi_post, "Top Tech Internships")
    assert len(opportunities) == 3

    # Check Opportunity 1
    opp1 = opportunities[0]
    assert "Machine Learning" in opp1["title"]
    assert "Google" in (opp1["organization"] or opp1["title"])
    assert "Python" in opp1["required_skills"]
    assert "PyTorch" in opp1["required_skills"]
    assert opp1["deadline"] == "Nov 30, 2026"
    assert opp1["direct_url"] == "https://careers.google.com/jobs/101"

    # Check Opportunity 2
    opp2 = opportunities[1]
    assert "Backend" in opp2["title"]
    assert "Stripe" in (opp2["organization"] or opp2["title"])
    assert "Go" in opp2["required_skills"]
    assert opp2["direct_url"] == "https://stripe.com/jobs/intern-backend"

def test_hackathon_extraction_and_stats(client, user_token):
    """Verify hackathon opportunity extraction, classification, and stats counting"""
    hackathon_text = """
    Gemini Developer Global Hackathon
    Organization: Google Cloud
    Theme: Building agentic AI systems
    Prize Pool: $100,000 in prizes
    Required Skills: Python, FastAPI, Docker
    Apply: https://devpost.com/software/gemini-hack
    Deadline: Nov 15, 2026
    """
    opps = heuristic_extract_opportunities(hackathon_text, "Devpost Hackathon")
    assert len(opps) == 1
    opp = opps[0]
    assert opp["type"] == "hackathon"
    assert "Gemini" in opp["title"]
    assert "100,000" in (opp["compensation"] or "")
    assert opp["deadline"] == "Nov 15, 2026"
    assert "Python" in opp["required_skills"]

    # Test saving via API and verify stats counter
    headers = {"Authorization": f"Bearer {user_token}"}
    r = client.post("/api/v1/resources", json={
        "title": "HackMIT 2026",
        "organization": "MIT",
        "type": "hackathon",
        "compensation": "$20,000 in prizes",
        "deadline": "Oct 12, 2026"
    }, headers=headers)
    assert r.status_code == 200

    stats = client.get("/api/v1/stats", headers=headers).json()
    assert stats["hackathons_saved"] >= 1

def test_missing_facts_not_invented():
    """Verify that if deadline or salary is omitted, it remains null/None, never invented"""
    text_without_deadline = """
    Software Engineering Intern @ Meta
    Required skills: React, TypeScript, GraphQL.
    Apply online at careers.
    """
    opps = heuristic_extract_opportunities(text_without_deadline)
    assert len(opps) == 1
    assert opps[0]["deadline"] is None
    assert opps[0]["compensation"] is None

def test_collection_creation_and_resource_association(client, user_token):
    """Verify many-to-many relationship: resource can belong to collections, and deleting collection preserves resource"""
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Create collection
    col_res = client.post("/api/v1/collections", json={"name": "Winter 2026 Applications", "color": "purple"}, headers=headers)
    assert col_res.status_code == 200
    col_id = col_res.json()["id"]

    # 2. Create resource
    res_payload = {
        "title": "AI Research Fellow",
        "organization": "Open Institute",
        "type": "internship",
        "required_skills": ["Python", "PyTorch"],
        "collection_ids": [col_id]
    }
    r_res = client.post("/api/v1/resources", json=res_payload, headers=headers)
    assert r_res.status_code == 200
    resource_id = r_res.json()["id"]

    # Verify resource has collection
    get_res = client.get(f"/api/v1/resources/{resource_id}", headers=headers)
    assert len(get_res.json()["collections"]) == 1
    assert get_res.json()["collections"][0]["id"] == col_id

    # 3. Delete collection
    del_col = client.delete(f"/api/v1/collections/{col_id}", headers=headers)
    assert del_col.status_code == 200

    # 4. Verify underlying resource still exists safely!
    after_del_res = client.get(f"/api/v1/resources/{resource_id}", headers=headers)
    assert after_del_res.status_code == 200
    assert after_del_res.json()["title"] == "AI Research Fellow"

def test_application_status_persistence(client, user_token):
    """Verify application tracking status changes persist correctly"""
    headers = {"Authorization": f"Bearer {user_token}"}

    # Create resource
    r_res = client.post("/api/v1/resources", json={"title": "Cloud Architect Intern", "type": "internship"}, headers=headers)
    res_id = r_res.json()["id"]

    # Create application
    app_res = client.post("/api/v1/applications", json={"resource_id": res_id, "status": "Applied", "notes": "Applied via referral"}, headers=headers)
    assert app_res.status_code == 200
    app_id = app_res.json()["id"]
    assert app_res.json()["status"] == "Applied"

    # Update to Interview
    patch_res = client.patch(f"/api/v1/applications/{app_id}", json={"status": "Interview", "notes": "Technical round scheduled"}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Interview"

    # Verify listing reflects interview
    list_apps = client.get("/api/v1/applications", headers=headers)
    assert any(a["id"] == app_id and a["status"] == "Interview" for a in list_apps.json())

def test_resume_update_recalculates_recommendations(db_session, test_user):
    """Verify transparent formula S = 0.35K + 0.25P + 0.20G + 0.10L + 0.10C updates with skills"""
    # Create internship requiring Python and PyTorch
    internship = Resource(
        user_id=test_user.id,
        title="ML Engineer Intern",
        type="internship",
        required_skills=["Python", "PyTorch"],
        location="Remote"
    )
    db_session.add(internship)
    db_session.commit()

    # User profile without resume initially
    rec_before = calculate_recommendation(internship, test_user.profile, [], None)
    
    # Now user uploads resume with Python and PyTorch + ML Project
    resume = Resume(
        user_id=test_user.id,
        version_name="ML Resume",
        parsed_data={
            "technical_skills": ["Python", "PyTorch"],
            "projects": [{"title": "Diabetes ML Classifier", "description": "Trained PyTorch and scikit-learn models."}],
            "graduation_year": 2026
        }
    )
    db_session.add(resume)
    db_session.commit()

    rec_after = calculate_recommendation(internship, test_user.profile, [], resume)
    
    # Matching skills should be detected and fit score should increase significantly
    assert "Python" in rec_after["matching_skills"]
    assert "Pytorch" in rec_after["matching_skills"]
    assert rec_after["fit_score"] > rec_before["fit_score"]
    assert rec_after["skill_score"] == 100.0

def test_user_data_isolation(client, db_session, test_user, user_token):
    """Verify User B cannot access or modify User A's resources"""
    headers_user_a = {"Authorization": f"Bearer {user_token}"}
    
    # Create Resource belonging to User A
    res_a = client.post("/api/v1/resources", json={"title": "User A Private Opportunity", "type": "job"}, headers=headers_user_a).json()
    res_a_id = res_a["id"]

    # Create User B
    user_b = User(email="userb@example.com", hashed_password=hash_password("pw123"), full_name="User B")
    db_session.add(user_b)
    db_session.commit()
    user_b_token = create_access_token(user_b.id)
    headers_user_b = {"Authorization": f"Bearer {user_b_token}"}

    # User B tries to get User A's resource -> 404
    resp = client.get(f"/api/v1/resources/{res_a_id}", headers=headers_user_b)
    assert resp.status_code == 404

    # User B tries to delete User A's resource -> 404
    del_resp = client.delete(f"/api/v1/resources/{res_a_id}", headers=headers_user_b)
    assert del_resp.status_code == 404

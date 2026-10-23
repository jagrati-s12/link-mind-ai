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

def test_job_extraction_and_stats(client, user_token):
    """Verify full-time job opportunity extraction, classification as 'job', and stats counting"""
    job_text = """
    Senior Full Stack Engineer
    Company: Stripe
    Employment Type: Full-time
    Location: Seattle, WA
    Salary: $185,000 - $220,000
    Required Skills: TypeScript, React, Python, PostgreSQL, System Design
    Apply: https://stripe.com/jobs/senior-fs-engineer
    """
    opps = heuristic_extract_opportunities(job_text, "Senior Full Stack Engineer @ Stripe")
    assert len(opps) == 1
    opp = opps[0]
    assert opp["type"] == "job"
    assert "Full Stack Engineer" in opp["title"]
    assert "Seattle" in (opp["location"] or "")
    assert "185,000" in (opp["compensation"] or "")

    headers = {"Authorization": f"Bearer {user_token}"}
    r = client.post("/api/v1/resources", json={
        "title": "Staff Backend Engineer",
        "organization": "Airbnb",
        "type": "job",
        "location": "San Francisco, CA",
        "compensation": "$230,000/year",
        "deadline": "Dec 31, 2026"
    }, headers=headers)
    assert r.status_code == 200

    stats = client.get("/api/v1/stats", headers=headers).json()
    assert stats["jobs_saved"] >= 1

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

def test_auth_registration_and_login(client):
    """Test user registration and subsequent login"""
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "New User"
    })
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["access_token"] is not None
    assert reg_data["email"] == "newuser@example.com"
    assert reg_data["is_totp_enabled"] is False

    # Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "newuser@example.com",
        "password": "securepassword123"
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["access_token"] is not None
    assert login_resp.json()["requires_2fa"] is False

def test_google_authenticator_totp_flow(client, db_session):
    """Test full Google Authenticator 2FA setup, verification, and 2FA login challenge"""
    import pyotp
    
    # 1. Register a new user
    reg = client.post("/api/v1/auth/register", json={
        "email": "totp_user@example.com",
        "password": "Password123!",
        "full_name": "TOTP Student"
    }).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check 2FA status (initially False)
    status_resp = client.get("/api/v1/auth/2fa/status", headers=headers).json()
    assert status_resp["is_totp_enabled"] is False

    # 3. Request 2FA Setup (generates QR code and secret)
    setup_resp = client.get("/api/v1/auth/2fa/setup", headers=headers)
    assert setup_resp.status_code == 200
    setup_data = setup_resp.json()
    assert "secret" in setup_data
    assert "qr_code" in setup_data
    assert setup_data["qr_code"].startswith("data:image/png;base64,")
    assert "LinkMind%20AI" in setup_data["otpauth_url"]
    secret = setup_data["secret"]

    # 4. Try enabling with an invalid code -> should fail with 400
    bad_verify = client.post("/api/v1/auth/2fa/enable", json={"code": "000000"}, headers=headers)
    assert bad_verify.status_code == 400

    # 5. Generate valid code with pyotp and enable 2FA
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    enable_resp = client.post("/api/v1/auth/2fa/enable", json={"code": valid_code}, headers=headers)
    assert enable_resp.status_code == 200
    assert enable_resp.json()["success"] is True

    # 6. Verify 2FA status is now True
    status_resp2 = client.get("/api/v1/auth/2fa/status", headers=headers).json()
    assert status_resp2["is_totp_enabled"] is True

    # 7. Try regular login without code -> should return requires_2fa=True & temp_token
    login_challenge = client.post("/api/v1/auth/login", json={
        "email": "totp_user@example.com",
        "password": "Password123!"
    })
    assert login_challenge.status_code == 200
    challenge_data = login_challenge.json()
    assert challenge_data["requires_2fa"] is True
    assert challenge_data["temp_token"] is not None
    assert challenge_data["access_token"] is None
    temp_token = challenge_data["temp_token"]

    # 8. Complete 2FA login via /2fa/verify-login with invalid code -> 401
    bad_login_2fa = client.post("/api/v1/auth/2fa/verify-login", json={
        "temp_token": temp_token,
        "code": "999999"
    })
    assert bad_login_2fa.status_code == 401

    # 9. Complete 2FA login via /2fa/verify-login with valid code -> 200 with access token
    good_code = totp.now()
    good_login_2fa = client.post("/api/v1/auth/2fa/verify-login", json={
        "temp_token": temp_token,
        "code": good_code
    })
    assert good_login_2fa.status_code == 200
    assert good_login_2fa.json()["access_token"] is not None

    # 10. Direct login with email + password + code all in one call
    direct_code = totp.now()
    direct_resp = client.post("/api/v1/auth/login", json={
        "email": "totp_user@example.com",
        "password": "Password123!",
        "code": direct_code
    })
    assert direct_resp.status_code == 200
    assert direct_resp.json()["access_token"] is not None
    assert direct_resp.json()["requires_2fa"] is False

    # 11. Disable 2FA with current valid code
    disable_code = totp.now()
    disable_resp = client.post("/api/v1/auth/2fa/disable", json={"code": disable_code}, headers=headers)
    assert disable_resp.status_code == 200
    assert disable_resp.json()["success"] is True

    # Check status is disabled
    status_resp3 = client.get("/api/v1/auth/2fa/status", headers=headers).json()
    assert status_resp3["is_totp_enabled"] is False

def test_course_tracker_and_isolation_from_applications(client, user_token):
    """Verify that courses are tracked in Course Tracker and completely isolated from Internship Applications"""
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Save a Course
    course_resp = client.post("/api/v1/resources", json={
        "title": "Machine Learning Specialization",
        "organization": "DeepLearning.AI",
        "type": "course",
        "taught_skills": ["Python", "Supervised Learning", "Linear Regression"]
    }, headers=headers)
    assert course_resp.status_code == 200
    course_id = course_resp.json()["id"]

    # 2. Save an Internship
    intern_resp = client.post("/api/v1/resources", json={
        "title": "Software Engineering Intern",
        "organization": "Microsoft",
        "type": "internship",
        "location": "Redmond, WA",
        "deadline": "Dec 15, 2026"
    }, headers=headers)
    assert intern_resp.status_code == 200
    intern_id = intern_resp.json()["id"]

    # 3. Check /applications: MUST ONLY contain the internship, NOT the course
    apps = client.get("/api/v1/applications", headers=headers).json()
    app_resource_ids = [a["resource_id"] for a in apps]
    assert intern_id in app_resource_ids
    assert course_id not in app_resource_ids

    # 4. Attempting to force-create an application for the course should return 400
    bad_app = client.post("/api/v1/applications", json={"resource_id": course_id}, headers=headers)
    assert bad_app.status_code == 400

    # 5. Check /course-tracker: auto-syncs the course
    tracked = client.get("/api/v1/course-tracker", headers=headers).json()
    tracked_ids = [t["resource_id"] for t in tracked]
    assert course_id in tracked_ids

    course_item = next(t for t in tracked if t["resource_id"] == course_id)
    assert course_item["status"] in ("In Progress", "Not Started")

    # 6. Update course progress milestone and %
    update_resp = client.put(f"/api/v1/course-tracker/{course_item['id']}", json={
        "progress_percentage": 60,
        "current_module": "Week 2: Cost Function",
        "notes": "Completed quiz 1 with 100%"
    }, headers=headers)
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["progress_percentage"] == 60
    assert updated_data["current_module"] == "Week 2: Cost Function"
    assert "Completed quiz" in updated_data["notes"]

def test_model_continuous_learning_and_feedback(client, user_token, db_session):
    """Verify that human feedback trains models dynamically and updates opportunity classifications"""
    from app.services.learning_engine import get_few_shot_prompt_examples

    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Create a resource with initially questionable classification
    res = client.post("/api/v1/resources", json={
        "title": "Graduate Systems Engineer",
        "organization": "Cisco",
        "type": "internship",
        "direct_url": "https://jobs.cisco.com/role/123",
        "location": "San Jose, CA"
    }, headers=headers).json()
    res_id = res["id"]

    # 2. User reviews listing and submits a correction: "This is a full-time job, not an internship"
    feedback_resp = client.post("/api/v1/feedback", json={
        "resource_id": res_id,
        "is_correct": False,
        "corrected_type": "job",
        "corrected_title": "Graduate Systems Engineer (Full-time)",
        "reason": "Full-time engineering job, not internship",
        "notes": "Learned from user correction"
    }, headers=headers)
    assert feedback_resp.status_code == 200
    fb_data = feedback_resp.json()
    assert fb_data["is_correct"] is False
    assert fb_data["corrected_type"] == "job"
    assert fb_data["domain"] == "jobs.cisco.com"

    # 3. Verify the resource itself has been reclassified in the database & title updated
    updated_res = client.get(f"/api/v1/resources/{res_id}", headers=headers).json()
    assert updated_res["type"] == "job"
    assert "Full-time" in updated_res["title"]
    assert updated_res["verification_status"] == "verified"

    # 4. Check feedback stats endpoint
    stats = client.get("/api/v1/feedback/stats", headers=headers).json()
    assert stats["total_feedback_count"] >= 1
    assert stats["user_corrections_count"] >= 1
    assert stats["active_few_shot_examples"] >= 1

    # 5. Verify the continuous learning engine generates few-shot prompts from this correction
    few_shot = get_few_shot_prompt_examples(db_session)
    assert "Graduate Systems Engineer" in few_shot
    assert "Correct type is 'job'" in few_shot
    assert "jobs.cisco.com" in few_shot

def test_curated_course_catalog_and_section_folders_extraction(client, user_token, db_session):
    """Verify that curated course catalogs (like awesome-courses) split into distinct courses with folder collections"""
    from app.services.ai_adapter import extract_markdown_curated_courses
    from app.services.extractor import process_source
    from app.models import Source, Resource, Collection

    sample_awesome_courses = """
# Awesome CS Courses

Introduction
------------
Curated list of university courses.

Courses
-------

### Systems

- [CS 61C](http://www-inst.eecs.berkeley.edu/~cs61c/sp15/) **Great Ideas in Computer Architecture (Machine Structures)** *UC Berkeley* <img src="videos.png" alt="Lecture Videos" />
    - The subjects covered in this course include: C and assembly language programming, translation of high-level programs into machine language.
    - [Lecture Videos](http://archive.org/cs61c)
    - [Assignments](http://cs61c/hw)

- [CS 140](http://www.scs.stanford.edu/14wi-cs140/) **Operating Systems** *Stanford University*
    - Introduces basic facilities provided in modern operating systems: concurrency, virtual memory, file systems.

### Machine Learning

- [CS 229](http://cs229.stanford.edu/) **Machine Learning** *Stanford University*
    - Comprehensive introduction to machine learning, supervised learning, and neural networks.
    """

    courses = extract_markdown_curated_courses(sample_awesome_courses, "prakhar1989/awesome-courses", "https://github.com/prakhar1989/awesome-courses")
    assert len(courses) == 3

    # Check Course 1
    c1 = courses[0]
    assert c1["type"] == "course"
    assert "CS 61C" in c1["title"]
    assert "Computer Architecture" in c1["title"]
    assert c1["organization"] == "UC Berkeley"
    assert c1["section"] == "Systems"
    assert c1["direct_url"] == "http://www-inst.eecs.berkeley.edu/~cs61c/sp15/"

    # Check Course 3
    c3 = courses[2]
    assert "CS 229" in c3["title"]
    assert c3["section"] == "Machine Learning"
    assert c3["organization"] == "Stanford University"

    # Test full end-to-end ingestion and folder creation
    source = Source(
        user_id=1,
        source_type="text",
        original_url=None,
        title="Awesome CS Courses",
        raw_content=sample_awesome_courses
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    # Ingest
    import asyncio
    asyncio.run(process_source(db_session, source.id))

    # Verify courses were persisted as distinct items
    saved_c1 = db_session.query(Resource).filter(Resource.direct_url == c1["direct_url"]).first()
    assert saved_c1 is not None
    assert saved_c1.type == "course"

    # Verify section collections (folders) exist and were attached
    c1_collections = [col.name for col in saved_c1.collections]
    assert "Systems" in c1_collections
    assert "Courses" in c1_collections

    saved_c3 = db_session.query(Resource).filter(Resource.direct_url == c3["direct_url"]).first()
    c3_collections = [col.name for col in saved_c3.collections]
    assert "Machine Learning" in c3_collections
    assert "Courses" in c3_collections




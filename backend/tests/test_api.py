import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.services.seed_data import seed_database
from app.models import User, UserRole
from app.config import Settings

@pytest.fixture(scope="module")
def client():
    # Setup test database tables & seed
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    
    with TestClient(app) as test_client:
        yield test_client

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "interactive_docs" in data

def test_auth_login_and_me(client):
    login_res = client.post("/api/v1/auth/login", json={
        "username": "dr_patil",
        "password": "Linguist123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "dr_patil"

def test_auth_admin_and_invalid_password(client):
    bad_res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrong_password_xyz"
    })
    assert bad_res.status_code == 401

    admin_res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    assert admin_res.status_code == 200
    assert admin_res.json()["user"]["role"] == "Admin"

def test_role_escalation_prevention(client):
    # Ensure clean test state by cleaning any previous test users
    db = SessionLocal()
    db.query(User).filter(User.username.in_(["escalate_admin_tester", "escalate_linguist_tester"])).delete()
    db.commit()
    db.close()

    # Attempting to register as Admin must fail to escalate and assign Contributor
    res1 = client.post("/api/v1/auth/register", json={
        "username": "escalate_admin_tester",
        "full_name": "Wannabe Admin",
        "email": "escalate_admin@test.com",
        "password": "SecurePassword123!",
        "role": "Admin"
    })
    assert res1.status_code == 201
    user1 = res1.json()
    assert user1["role"] == "Contributor"

    # Attempting to register as Linguist must also assign Contributor
    res2 = client.post("/api/v1/auth/register", json={
        "username": "escalate_linguist_tester",
        "full_name": "Wannabe Linguist",
        "email": "escalate_linguist@test.com",
        "password": "SecurePassword123!",
        "role": "Linguist"
    })
    assert res2.status_code == 201
    user2 = res2.json()
    assert user2["role"] == "Contributor"

def test_admin_promotes_user_role(client):
    # 1. Non-admin attempting to promote fails with 403
    user_login = client.post("/api/v1/auth/login", json={
        "username": "escalate_admin_tester",
        "password": "SecurePassword123!"
    })
    assert user_login.status_code == 200
    user_token = user_login.json()["access_token"]

    promote_attempt = client.put(
        "/api/v1/auth/users/1/role",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"role": "Linguist"}
    )
    assert promote_attempt.status_code == 403
    assert "Forbidden" in promote_attempt.json()["detail"]

    # 2. Admin successfully promotes user to Linguist
    admin_login = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    # Target user created in previous test
    db = SessionLocal()
    target_user = db.query(User).filter(User.username == "escalate_linguist_tester").first()
    target_id = target_user.id
    db.close()

    admin_promote = client.put(
        f"/api/v1/auth/users/{target_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "Linguist"}
    )
    assert admin_promote.status_code == 200
    assert admin_promote.json()["role"] == "Linguist"

    # 3. Invalid role returns 400
    bad_role = client.put(
        f"/api/v1/auth/users/{target_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "SuperUser"}
    )
    assert bad_role.status_code == 400

def test_voting_requires_auth_and_updates_counter(client):
    # Retrieve a vocabulary entry to vote on
    lex_res = client.get("/api/v1/lexicon/?limit=1")
    assert lex_res.status_code == 200
    entry_id = lex_res.json()[0]["id"]
    initial_upvotes = lex_res.json()[0]["upvotes"]

    # 1. Unauthenticated vote request must fail with 401
    unauth_vote = client.post(f"/api/v1/lexicon/{entry_id}/vote?vote_type=1")
    assert unauth_vote.status_code == 401

    # 2. Authenticated vote succeeds and increments upvotes
    login_res = client.post("/api/v1/auth/login", json={
        "username": "dr_patil",
        "password": "Linguist123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    vote_res = client.post(f"/api/v1/lexicon/{entry_id}/vote?vote_type=1", headers=headers)
    assert vote_res.status_code == 200
    vote_data = vote_res.json()
    assert vote_data["user_vote"] == 1
    assert vote_data["upvotes"] >= initial_upvotes

def test_audio_upload_backend_validation(client):
    # 1. Invalid audio extension must return 400 Bad Request
    bad_ext_res = client.post(
        "/api/voices",
        files={"file": ("malicious_script.sh", b"echo 'hack'", "text/x-shellscript")}
    )
    assert bad_ext_res.status_code == 400
    assert "Invalid audio file type" in bad_ext_res.json()["detail"]

    # 2. Empty audio file must return 400 Bad Request
    empty_res = client.post(
        "/api/voices",
        files={"file": ("empty.wav", b"", "audio/wav")}
    )
    assert empty_res.status_code == 400
    assert "cannot be empty" in empty_res.json()["detail"]

    # 3. Oversized audio file (> 25MB) must return 413 Payload Too Large
    huge_payload = b"0" * (25 * 1024 * 1024 + 1024)
    oversized_res = client.post(
        "/api/voices",
        files={"file": ("oversized.wav", huge_payload, "audio/wav")}
    )
    assert oversized_res.status_code == 413
    assert "exceeds maximum allowed limit" in oversized_res.json()["detail"]

    # 4. Valid audio upload must succeed with 201 Created
    valid_res = client.post(
        "/api/voices",
        files={"file": ("valid_sample.wav", b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00data\x00\x00\x00\x00", "audio/wav")},
        data={"variety": "Malvani", "transcript": "सुंदर निसर्ग"}
    )
    assert valid_res.status_code == 201
    assert "id" in valid_res.json()
    assert "audio_file" in valid_res.json()

def test_production_security_and_database_config():
    # 1. PostgreSQL URL prefix normalization (postgres:// -> postgresql://)
    test_pg_url = "postgres://roottalk_user:secret_pass@ep-server.render.com:5432/roottalk"
    os.environ["DATABASE_URL"] = test_pg_url
    os.environ["ENVIRONMENT"] = "development"
    
    test_settings = Settings()
    assert test_settings.DATABASE_URL.startswith("postgresql://")
    assert not test_settings.DATABASE_URL.startswith("postgres://")
    
    del os.environ["DATABASE_URL"]

    # 2. Production environment strictly requires explicit, non-default SECRET_KEY
    os.environ["ENVIRONMENT"] = "production"
    os.environ["SECRET_KEY"] = "preservation_secret_key_super_secure_2026_regional_linguistics"
    
    with pytest.raises(RuntimeError) as exc_info:
        Settings()
    assert "In production environment, a secure SECRET_KEY" in str(exc_info.value)
    
    # Clean up environment variables
    os.environ["ENVIRONMENT"] = "development"
    os.environ["SECRET_KEY"] = "preservation_dev_secret_key_2026_regional_linguistics"

def test_list_dialects(client):
    response = client.get("/api/v1/dialects/")
    assert response.status_code == 200
    dialects = response.json()
    assert len(dialects) >= 4
    malvani = next(d for d in dialects if d["code"] == "mar-mal")
    assert malvani["name"] == "Malvani"
    assert malvani["preservation_score"] > 0

def test_dialect_map_data(client):
    dialects_res = client.get("/api/v1/dialects/")
    d_id = dialects_res.json()[0]["id"]
    
    map_res = client.get(f"/api/v1/dialects/{d_id}/map-data")
    assert map_res.status_code == 200
    map_data = map_res.json()
    assert "coordinates" in map_data
    assert map_data["coordinates"]["latitude"] is not None

def test_lexicon_and_ipa_generation(client):
    ipa_res = client.post("/api/v1/lexicon/ipa-generate?text=ख़य चाललोस?")
    assert ipa_res.status_code == 200
    assert "ipa_transcription" in ipa_res.json()

    lex_res = client.get("/api/v1/lexicon/")
    assert lex_res.status_code == 200
    assert len(lex_res.json()) >= 1

def test_lexicon_pagination_headers(client):
    res = client.get("/api/v1/lexicon/?page=1&limit=10")
    assert res.status_code == 200
    assert "X-Total-Count" in res.headers
    assert "X-Total-Pages" in res.headers
    assert "X-Current-Page" in res.headers
    assert int(res.headers["X-Total-Count"]) >= 100
    assert int(res.headers["X-Total-Pages"]) >= 10
    assert res.headers["X-Current-Page"] == "1"
    assert len(res.json()) == 10

def test_phonetic_search(client):
    res_lat = client.post("/api/v1/lexicon/phonetic-search", json={
        "query_term": "khay",
        "max_distance": 3
    })
    assert res_lat.status_code == 200
    results_lat = res_lat.json()
    assert isinstance(results_lat, list)

    res_dev = client.post("/api/v1/lexicon/phonetic-search", json={
        "query_term": "आंबा",
        "max_distance": 3
    })
    assert res_dev.status_code == 200
    results_dev = res_dev.json()
    assert len(results_dev) >= 1
    assert any("आंबा" in r["term"] for r in results_dev)

def test_public_contribution_and_peer_verification(client):
    from app.models import Entry
    db = SessionLocal()
    db.query(Entry).filter(Entry.word == "गुपित_नवीन").delete()
    db.commit()
    db.close()

    post_res = client.post("/api/v1/lexicon/", json={
        "dialect_id": 1,
        "term": "गुपित_नवीन",
        "meaning_en": "Fresh secret mystery",
        "meaning_standard_lang": "गूढ / रहस्य",
        "semantic_category": "Culture",
        "part_of_speech": "Noun",
        "example_sentence_dialect": "ह्या झाडाखाली एक गुपित दडलंय."
    })
    assert post_res.status_code == 201
    entry = post_res.json()
    assert entry["verification_status"] == "Pending"
    entry_id = entry["id"]

    admin_login = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    assert admin_login.status_code == 200
    token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    verify_res = client.post(f"/api/v1/contributions/verify-lexicon/{entry_id}?approve=true", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "Verified"

def test_audio_archive_and_subtitles(client):
    audios_res = client.get("/api/v1/audio-archive/")
    assert audios_res.status_code == 200
    audios = audios_res.json()
    assert len(audios) >= 1
    
    audio_id = audios[0]["id"]
    
    srt_res = client.get(f"/api/v1/audio-archive/{audio_id}/subtitles.srt")
    assert srt_res.status_code == 200
    assert "-->" in srt_res.text

    vtt_res = client.get(f"/api/v1/audio-archive/{audio_id}/subtitles.vtt")
    assert vtt_res.status_code == 200
    assert "WEBVTT" in vtt_res.text

def test_quizzes(client):
    decks_res = client.get("/api/v1/quizzes/decks")
    assert decks_res.status_code == 200
    decks = decks_res.json()
    assert len(decks) >= 1

    deck = decks[0]

    answers_payload = [
        {"question_id": q["id"], "selected_option": "B"}
        for q in deck["questions"]
    ]
    submit_res = client.post("/api/v1/quizzes/submit", json={
        "deck_id": deck["id"],
        "answers": answers_payload
    })
    assert submit_res.status_code == 200
    res_data = submit_res.json()
    assert res_data["correct_count"] == len(deck["questions"])
    assert res_data["score_percentage"] == 100.0

def test_analytics_and_export(client):
    stats_res = client.get("/api/v1/analytics/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_dialects"] >= 4

    json_export = client.get("/api/v1/analytics/export/json")
    assert json_export.status_code == 200
    assert "dialect" in json_export.text

    csv_export = client.get("/api/v1/analytics/export/csv")
    assert csv_export.status_code == 200
    assert "Dialect Code" in csv_export.text

def test_categories_and_contributors_endpoints(client):
    cat_res = client.get("/api/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json()
    assert len(categories) == 15
    assert any(c["count"] > 0 for c in categories)

    cont_res = client.get("/api/contributors")
    assert cont_res.status_code == 200
    contributors = cont_res.json()
    assert len(contributors) >= 3
    assert any(c["name"] == "Parth Kadam" for c in contributors)

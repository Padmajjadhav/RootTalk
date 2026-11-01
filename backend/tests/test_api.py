import os
import sys
import tempfile
import sqlite3
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings, Settings
from app.database import Base, get_db
from app.models import User, UserRole, Entry, LexiconEntry, AudioArchive, VerificationStatus
from app.services.seed_data import seed_database
from app.services.rate_limiter import rate_limiter

# Initial snapshot of dev db path for isolation test
DEV_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "preservation.db"))

@pytest.fixture(scope="session")
def test_env():
    """
    Session-level fixture that isolates tests completely from the development/production database:
    1. Creates a temporary directory for test database and audio files.
    2. Overrides database engine and sessionmaker to point to the isolated test database.
    3. Overrides upload directories to avoid polluting production uploads.
    4. Seeds the test database with standard initial data.
    5. Cleans up temporary files and restores dependencies upon completion.
    """
    temp_dir = tempfile.TemporaryDirectory()
    test_db_path = os.path.join(temp_dir.name, "test_preservation.sqlite")
    test_upload_dir = os.path.join(temp_dir.name, "uploads")
    test_audio_dir = os.path.join(test_upload_dir, "audio")
    os.makedirs(test_audio_dir, exist_ok=True)

    # Save original settings
    orig_upload_dir = settings.UPLOAD_DIR
    orig_audio_upload_dir = settings.AUDIO_UPLOAD_DIR
    settings.UPLOAD_DIR = test_upload_dir
    settings.AUDIO_UPLOAD_DIR = test_audio_dir

    # Create isolated test engine and sessionmaker
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create schema and seed isolated database
    Base.metadata.create_all(bind=test_engine)
    init_db = TestingSessionLocal()
    seed_database(init_db)
    init_db.close()

    # FastAPI dependency override
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield {
        "engine": test_engine,
        "SessionLocal": TestingSessionLocal,
        "temp_dir": temp_dir,
        "upload_dir": test_upload_dir,
        "audio_dir": test_audio_dir
    }

    # Teardown: clear overrides, dispose engine, cleanup temp directory
    app.dependency_overrides.clear()
    test_engine.dispose()
    settings.UPLOAD_DIR = orig_upload_dir
    settings.AUDIO_UPLOAD_DIR = orig_audio_upload_dir
    temp_dir.cleanup()

@pytest.fixture(scope="session")
def client(test_env):
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


def test_jwt_expired_and_invalid_tokens(client):
    from datetime import timedelta
    from app.services.auth_service import create_access_token

    # 1. Malformed / invalid token must return 401 Unauthorized
    invalid_headers = {"Authorization": "Bearer malformed.invalid.token"}
    res_invalid = client.get("/api/v1/auth/me", headers=invalid_headers)
    assert res_invalid.status_code == 401
    assert "Could not validate credentials" in res_invalid.json()["detail"]

    # 2. Expired JWT token (expired in the past) must return 401 Unauthorized
    expired_token = create_access_token(
        data={"sub": "dr_patil", "role": "Linguist"},
        expires_delta=timedelta(seconds=-60)
    )
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    res_expired = client.get("/api/v1/auth/me", headers=expired_headers)
    assert res_expired.status_code == 401
    assert "Could not validate credentials" in res_expired.json()["detail"]

    # 3. Missing authorization header on protected route returns 401 Unauthorized
    res_no_token = client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    # 4. Confirm sensitive password hash is never exposed in user responses
    login_res = client.post("/api/v1/auth/login", json={
        "username": "dr_patil",
        "password": "Linguist123!"
    })
    assert login_res.status_code == 200
    user_payload = login_res.json()["user"]
    assert "hashed_password" not in user_payload
    assert "password" not in user_payload

    token = login_res.json()["access_token"]
    me_payload = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert "hashed_password" not in me_payload
    assert "password" not in me_payload


def test_role_escalation_prevention(client, test_env):
    # Public registration must always assign Contributor role; privilege self-selection ignored
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


def test_admin_promotes_user_role(client, test_env):
    # 1. Non-admin attempting to promote fails with 403 Forbidden
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

    SessionLocal = test_env["SessionLocal"]
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

    # 3. Invalid role returns 400 Bad Request
    bad_role = client.put(
        f"/api/v1/auth/users/{target_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "SuperUser"}
    )
    assert bad_role.status_code == 400


def test_password_handling_bcrypt_limit(client):
    # Bcrypt maximum password length is 72 bytes.
    # Passwords exceeding 72 bytes must be rejected with validation errors (not silently truncated)
    over_72_pass = "A" * 73

    # 1. Registration with > 72 bytes password must be rejected
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "long_pwd_user",
        "email": "long_pwd@test.com",
        "password": over_72_pass
    })
    assert reg_res.status_code in [400, 422]
    assert "72 bytes" in str(reg_res.json())

    # 2. Login with > 72 bytes password must be rejected
    login_res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": over_72_pass
    })
    assert login_res.status_code in [400, 422]
    assert "72 bytes" in str(login_res.json())

    # 3. Valid password within 72 bytes registers cleanly
    valid_pass = "ValidPass123!_ सुरक्षित_पासवर्ड"  # Unicode text within 72 bytes
    reg_ok = client.post("/api/v1/auth/register", json={
        "username": "valid_pwd_user",
        "email": "valid_pwd@test.com",
        "password": valid_pass
    })
    assert reg_ok.status_code == 201


def test_voting_requires_auth_and_updates_counter(client):
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


def test_audio_content_validation_and_size_limits(client):
    # 1. Non-audio file extension must return 400 Bad Request
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

    # 3. Spoofed audio (text file disguised with .wav extension) must fail content validation
    spoofed_wav = client.post(
        "/api/voices",
        files={"file": ("spoofed.wav", b"This is just plain text content not genuine RIFF audio", "audio/wav")},
        data={"variety": "Malvani"}
    )
    assert spoofed_wav.status_code == 400
    assert "Audio content validation failed" in spoofed_wav.json()["detail"]

    # 4. Spoofed mp3 (text disguised as .mp3) must fail content validation
    spoofed_mp3 = client.post(
        "/api/voices",
        files={"file": ("spoofed.mp3", b"Not an mp3 file at all", "audio/mpeg")},
        data={"variety": "Malvani"}
    )
    assert spoofed_mp3.status_code == 400
    assert "Audio content validation failed" in spoofed_mp3.json()["detail"]

    # 5. Oversized audio file (> 25MB) must return 413 Payload Too Large
    huge_payload = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"0" * (25 * 1024 * 1024 + 1024)
    oversized_res = client.post(
        "/api/voices",
        files={"file": ("oversized.wav", huge_payload, "audio/wav")}
    )
    assert oversized_res.status_code == 413
    assert "exceeds maximum allowed limit" in oversized_res.json()["detail"]

    # 6. Valid audio file with genuine WAV header must succeed with 201 Created
    valid_wav_content = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    valid_res = client.post(
        "/api/voices",
        files={"file": ("valid_sample.wav", valid_wav_content, "audio/wav")},
        data={"variety": "Malvani", "transcript": "सुंदर निसर्ग"}
    )
    assert valid_res.status_code == 201
    assert "id" in valid_res.json()
    assert "audio_file" in valid_res.json()


def test_audio_stream_missing_and_existing_file(client, test_env):
    SessionLocal = test_env["SessionLocal"]
    db = SessionLocal()

    # Create an audio record whose file does not exist on disk
    missing_audio = AudioArchive(
        dialect_id=1,
        title="Missing File Story",
        genre="Folk Lore",
        audio_file_path="uploads/audio/definitely_nonexistent_audio_file.mp3",
        duration_seconds=30.0,
        verification_status=VerificationStatus.VERIFIED
    )
    db.add(missing_audio)
    db.commit()
    db.refresh(missing_audio)
    missing_id = missing_audio.id

    # 1. Streaming a missing audio file must strictly return HTTP 404 (no dummy audio fallback)
    missing_res = client.get(f"/api/v1/audio-archive/{missing_id}/stream")
    assert missing_res.status_code == 404
    assert "does not exist on storage disk" in missing_res.json()["detail"]

    # 2. Streaming an existing valid audio file returns 200 OK
    sample_filename = "real_stream_test.mp3"
    sample_disk_path = os.path.join(test_env["audio_dir"], sample_filename)
    # Genuine MP3 with ID3 header
    genuine_mp3_bytes = b"ID3\x04\x00\x00\x00\x00\x00\x0a" + (b"\xff\xfb\x90\x00" * 20)
    with open(sample_disk_path, "wb") as f:
        f.write(genuine_mp3_bytes)

    existing_audio = AudioArchive(
        dialect_id=1,
        title="Existing File Story",
        genre="Folk Lore",
        audio_file_path=os.path.join("uploads", "audio", sample_filename),
        duration_seconds=30.0,
        verification_status=VerificationStatus.VERIFIED
    )
    db.add(existing_audio)
    db.commit()
    db.refresh(existing_audio)
    existing_id = existing_audio.id
    db.close()

    existing_res = client.get(f"/api/v1/audio-archive/{existing_id}/stream")
    assert existing_res.status_code == 200
    assert existing_res.content == genuine_mp3_bytes


def test_public_rate_limiting(client):
    rate_limiter.reset()

    # Submit up to the maximum 10 allowed unauthenticated entries
    for i in range(10):
        res = client.post("/api/v1/lexicon/", json={
            "dialect_id": 1,
            "term": f"rate_limit_word_{i}",
            "meaning_en": f"Rate test meaning {i}",
            "meaning_standard_lang": "चाचणी",
            "semantic_category": "Daily Life",
            "part_of_speech": "Noun"
        })
        assert res.status_code == 201

    # 11th unauthenticated request must be rate-limited with HTTP 429
    limited_res = client.post("/api/v1/lexicon/", json={
        "dialect_id": 1,
        "term": "rate_limit_word_blocked",
        "meaning_en": "Blocked meaning",
        "meaning_standard_lang": "अडवलेला",
        "semantic_category": "Daily Life",
        "part_of_speech": "Noun"
    })
    assert limited_res.status_code == 429
    assert "Rate limit exceeded" in limited_res.json()["detail"]

    # Reset rate limiter after test
    rate_limiter.reset()


def test_websocket_activity_event_delivery(client):
    # Test WebSocket connection and event receipt
    with client.websocket_connect("/api/v1/ws/activity") as websocket:
        # First message upon connection is CONNECTED event
        conn_msg = websocket.receive_json()
        assert conn_msg.get("event") == "CONNECTED"

        # Submit a lexicon entry via client
        post_res = client.post("/api/v1/lexicon/", json={
            "dialect_id": 1,
            "term": "लाईव्ह_शब्द",
            "meaning_en": "Live word event",
            "meaning_standard_lang": "थेट शब्द",
            "semantic_category": "Culture",
            "part_of_speech": "Noun"
        })
        assert post_res.status_code == 201

        # The WebSocket should receive the standardized activity event
        activity_msg = websocket.receive_json()
        assert activity_msg.get("event") == "NEW_LEXICON_ENTRY"
        assert activity_msg.get("type") == "NEW_LEXICON_ENTRY"
        assert activity_msg.get("term") == "लाईव्ह_शब्द"


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
    
    # Restore dev environment
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
    ipa_res = client.post("/api/v1/lexicon/ipa-generate?term=काय चाललंय")
    assert ipa_res.status_code == 200
    assert "ipa" in ipa_res.json()

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
    questions = deck["questions"]
    assert len(questions) == 3

    # Answers matching the authentic questions (Q1: B, Q2: A, Q3: B)
    answers_payload = [
        {"question_id": questions[0]["id"], "selected_option": "B"},
        {"question_id": questions[1]["id"], "selected_option": "A"},
        {"question_id": questions[2]["id"], "selected_option": "B"},
    ]
    submit_res = client.post("/api/v1/quizzes/submit", json={
        "deck_id": deck["id"],
        "answers": answers_payload
    })
    assert submit_res.status_code == 200
    res_data = submit_res.json()
    assert res_data["correct_count"] == 3
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


def test_todays_word_retrieval(client):
    res = client.get("/api/v1/lexicon/?limit=20")
    assert res.status_code == 200
    entries = res.json()
    assert len(entries) >= 20
    sample = entries[0]
    assert "term" in sample
    assert "meaning_en" in sample
    assert "dialect_id" in sample
    assert "ipa_transcription" in sample


def test_dev_database_isolation():
    """
    Independent verification that the primary development database (backend/preservation.db)
    was strictly isolated and was NEVER touched or mutated by the test suite execution.
    """
    assert os.path.isfile(DEV_DB_PATH), f"Dev database not found at {DEV_DB_PATH}"
    conn = sqlite3.connect(DEV_DB_PATH)
    c = conn.cursor()

    users_count = c.execute("SELECT count(*) FROM users").fetchone()[0]
    entries_count = c.execute("SELECT count(*) FROM entries").fetchone()[0]
    voices_count = c.execute("SELECT count(*) FROM voice_recordings").fetchone()[0]
    votes_count = c.execute("SELECT count(*) FROM lexicon_votes").fetchone()[0]
    conn.close()

    # The dev database must have only authentic seed data and 0 test artifacts
    assert users_count == 5, f"Expected 5 genuine users in dev DB, found {users_count}"
    assert entries_count == 155, f"Expected 155 genuine entries in dev DB, found {entries_count}"
    assert voices_count == 9, f"Expected 9 genuine voices in dev DB, found {voices_count}"
    assert votes_count == 0, f"Expected 0 votes in dev DB, found {votes_count}"

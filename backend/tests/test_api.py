import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.services.seed_data import seed_database

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
    # Login with seeded user
    login_res = client.post("/api/v1/auth/login", json={
        "username": "dr_patil",
        "password": "Linguist123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Test /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "dr_patil"

def test_auth_admin_and_invalid_password(client):
    # Invalid password test
    bad_res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrong_password_xyz"
    })
    assert bad_res.status_code == 401

    # Valid admin login
    admin_res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    assert admin_res.status_code == 200
    assert admin_res.json()["user"]["role"] == "Admin"

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
    # IPA generation test
    ipa_res = client.post("/api/v1/lexicon/ipa-generate?text=ख़य चाललोस?")
    assert ipa_res.status_code == 200
    assert "ipa_transcription" in ipa_res.json()

    # List lexicon
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
    # Latin query
    res_lat = client.post("/api/v1/lexicon/phonetic-search", json={
        "query_term": "khay",
        "max_distance": 3
    })
    assert res_lat.status_code == 200
    results_lat = res_lat.json()
    assert isinstance(results_lat, list)

    # Devanagari query
    res_dev = client.post("/api/v1/lexicon/phonetic-search", json={
        "query_term": "आंबा",
        "max_distance": 3
    })
    assert res_dev.status_code == 200
    results_dev = res_dev.json()
    assert len(results_dev) >= 1
    assert any("आंबा" in r["term"] for r in results_dev)

def test_public_contribution_and_peer_verification(client):
    # 1. Anonymous public word submission
    post_res = client.post("/api/v1/lexicon/", json={
        "dialect_id": 1,
        "term": "गुपित",
        "meaning_en": "Secret or hidden mystery",
        "meaning_standard_lang": "गूढ / रहस्य",
        "semantic_category": "Culture",
        "part_of_speech": "Noun",
        "example_sentence_dialect": "ह्या झाडाखाली एक गुपित दडलंय."
    })
    assert post_res.status_code == 201
    entry = post_res.json()
    assert entry["verification_status"] == "Pending"
    entry_id = entry["id"]

    # 2. Login as Admin
    admin_login = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    assert admin_login.status_code == 200
    token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Verify / Approve submission
    verify_res = client.post(f"/api/v1/contributions/verify-lexicon/{entry_id}?approve=true", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "Verified"

def test_audio_archive_and_subtitles(client):
    audios_res = client.get("/api/v1/audio-archive/")
    assert audios_res.status_code == 200
    audios = audios_res.json()
    assert len(audios) >= 1
    
    audio_id = audios[0]["id"]
    
    # Test SRT subtitle download
    srt_res = client.get(f"/api/v1/audio-archive/{audio_id}/subtitles.srt")
    assert srt_res.status_code == 200
    assert "-->" in srt_res.text

    # Test VTT subtitle stream
    vtt_res = client.get(f"/api/v1/audio-archive/{audio_id}/subtitles.vtt")
    assert vtt_res.status_code == 200
    assert "WEBVTT" in vtt_res.text

def test_quizzes(client):
    decks_res = client.get("/api/v1/quizzes/decks")
    assert decks_res.status_code == 200
    decks = decks_res.json()
    assert len(decks) >= 1

    deck = decks[0]
    question = deck["questions"][0]

    # Submit quiz answers for all deck questions
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

    # Export JSON
    json_export = client.get("/api/v1/analytics/export/json")
    assert json_export.status_code == 200
    assert "dialect" in json_export.text

    # Export CSV
    csv_export = client.get("/api/v1/analytics/export/csv")
    assert csv_export.status_code == 200
    assert "Dialect Code" in csv_export.text

def test_categories_and_contributors_endpoints(client):
    # Test /api/categories
    cat_res = client.get("/api/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json()
    assert len(categories) == 15
    assert any(c["count"] > 0 for c in categories)

    # Test /api/contributors
    cont_res = client.get("/api/contributors")
    assert cont_res.status_code == 200
    contributors = cont_res.json()
    assert len(contributors) >= 3
    assert any(c["name"] == "Parth Kadam" for c in contributors)

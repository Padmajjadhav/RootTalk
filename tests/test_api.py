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

def test_list_dialects(client):
    response = client.get("/api/v1/dialects/")
    assert response.status_code == 200
    dialects = response.json()
    assert len(dialects) >= 4
    malvani = next(d for d in dialects if d["code"] == "mar-mal")
    assert malvani["name"] == "Malvani"
    assert malvani["preservation_score"] > 0

def test_dialect_map_data(client):
    # Fetch first dialect
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

def test_phonetic_search(client):
    res = client.post("/api/v1/lexicon/phonetic-search", json={
        "query_term": "khay",
        "max_distance": 3
    })
    assert res.status_code == 200
    results = res.json()
    assert isinstance(results, list)

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

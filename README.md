# 🎙️ Digital Preservation of Regional Languages & Dialects API Backend

A high-performance, interactive backend engine built with **FastAPI**, **SQLAlchemy**, **Pydantic V2**, **WebSockets**, and **SQLite** for preserving endangered regional languages, dialects, oral folklore, and phonetic heritage.

---

## 👥 Student / Project Team Details

| Student Name | Roll No. |
| :--- | :--- |
| **Aaditya Jadhav** | **59** |
| **Padmaj Jadhav** | **35** |
| **Parth Kadam** | **49** |

---

## 🚀 Key Features & Interactive Architecture

1. **Dialect Cartography & Registry (`/api/v1/dialects`)**
   - Registry for regional dialects (e.g. *Malvani*, *Varhadi*, *Ahirani*, *Awadhi*, *Bhojpuri*).
   - Endangerment status classification based on UNESCO scale (*Safe*, *Vulnerable*, *Definitely Endangered*, *Severely Endangered*, *Critically Endangered*, *Extinct*).
   - Geographic coordinates & cartographic map metadata for regional mapping.
   - Quantitative Preservation Index Score calculation per dialect (0–100 scale).

2. **Linguistic Dictionary Vault (`/api/v1/lexicon`)**
   - Preserves words, phrases, idioms (*Mhan/Proverbs*), and semantic terms.
   - **IPA Phonetic Generator**: Instant conversion of Devanagari regional script into International Phonetic Alphabet (IPA) representation.
   - **Indic Phonetic Search Engine**: Combines **Indic Soundex** and **Levenshtein Distance** algorithms to enable fuzzy searching for spoken accent variations.
   - Standard language translation equivalents and etymological metadata.

3. **Audio & Oral History Archive (`/api/v1/audio-archive`)**
   - Audio file upload (`.mp3`, `.wav`, `.m4a`, `.ogg`).
   - Waveform peak generator for amplitude visualization.
   - **HTTP Range-Request Audio Streaming (`/stream`)** for smooth media playback.
   - **Auto Subtitle Generator**: Export transcripts into `.srt` (SubRip) or `.vtt` (WebVTT) subtitle files on the fly.

4. **Peer Verification & Gamification (`/api/v1/contributions`)**
   - Peer review workflow for linguists to verify community contributions.
   - User reputation system, badges (*Linguistic Enthusiast*, *Dialect Champion*, *Preservation Master*), and top contributor leaderboards.

5. **Interactive Quizzes & Learning Decks (`/api/v1/quizzes`)**
   - Multiple choice quiz decks for dialect vocabulary & proverbs.
   - Automated score calculation, feedback, and bonus reputation points.

6. **Real-time WebSockets (`/api/v1/ws`)**
   - `/ws/activity`: System-wide live activity stream broadcasting real-time preservation events.
   - `/ws/dictation/{recording_id}`: Collaborative dictation room for live audio transcript editing.
   - `/ws/quiz/{deck_id}`: Multiplayer live trivia quiz room.

7. **Data Archives & Analytics (`/api/v1/analytics`)**
   - Preservation statistics and coverage breakdown.
   - Export full preservation database as **JSON** or **CSV** for researchers and academic archiving.

---

## 🛠️ Getting Started

### 1. Prerequisites & Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running the API Server
Start the backend server with auto-reload:
```bash
python run_server.py --port 8000 --reload
```

Server endpoints will be live at:
- **Interactive OpenAPI (Swagger) UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Interactive Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema JSON**: [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)

---

## 🧪 Running Automated Unit Tests

Run the Pytest suite to verify all 9 backend component tests:
```bash
.\venv\Scripts\pytest.exe -v
```

---

## 🔑 Default Seed Users & Credentials

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `Admin123!` | Admin | System Administrator |
| `dr_patil` | `Linguist123!` | Linguist | Senior Dialectologist & Verification Auditor |
| `konkan_preserver` | `User123!` | Contributor | Cultural Explorer & Dialect Collector |

---

## 📡 API Endpoint Overview

### 🔐 Auth (`/api/v1/auth`)
- `POST /auth/register` — Register a new contributor or linguist.
- `POST /auth/login` — Login and obtain JWT Bearer Token.
- `GET /auth/me` — Get profile and reputation score of the logged-in user.

### 🗺️ Dialects (`/api/v1/dialects`)
- `GET /dialects/` — List all registered regional dialects with preservation scores.
- `POST /dialects/` — Register a new regional dialect/language variant.
- `GET /dialects/{id}` — Retrieve detailed dialect metadata.
- `GET /dialects/{id}/map-data` — Cartographic map coordinates and district coverage payload.

### 📚 Lexicon Dictionary (`/api/v1/lexicon`)
- `GET /lexicon/` — Search & list preserved dialect terms and phrases.
- `POST /lexicon/` — Add a new word/phrase to the preserver.
- `POST /lexicon/ipa-generate` — Instant Devanagari script to IPA phonetic representation converter.
- `POST /lexicon/phonetic-search` — Phonetic search using Indic Soundex and Levenshtein distance.
- `POST /lexicon/{id}/vote` — Upvote / Downvote a term with peer review comments.

### 🎙️ Audio Archive (`/api/v1/audio-archive`)
- `GET /audio-archive/` — Search oral history recordings & folk songs.
- `POST /audio-archive/upload` — Upload an audio file with metadata & auto-generate amplitude waveform peaks.
- `GET /audio-archive/{id}/stream` — Stream audio with HTTP range requests.
- `GET /audio-archive/{id}/subtitles.srt` — Download auto-generated SRT subtitles.
- `GET /audio-archive/{id}/subtitles.vtt` — Stream WebVTT subtitles.

### 🏆 Peer Review & Leaderboard (`/api/v1/contributions`)
- `GET /contributions/pending-lexicon` — List pending terms for linguist review.
- `POST /contributions/verify-lexicon/{id}` — Verify or reject submission and award user reputation points.
- `GET /contributions/leaderboard` — Top dialect preservers ranked by reputation.

### 🎮 Quizzes & Trivia (`/api/v1/quizzes`)
- `GET /quizzes/decks` — List dialect quiz decks.
- `GET /quizzes/decks/{id}` — Fetch quiz questions.
- `POST /quizzes/submit` — Submit answers, calculate score, and earn bonus points.

### 📊 Analytics & Archives (`/api/v1/analytics`)
- `GET /analytics/stats` — Overall preservation statistics & coverage breakdown.
- `GET /analytics/preservation-index/{dialect_id}` — Quantitative Preservation Score breakdown.
- `GET /analytics/export/json` — Export full preservation archive as JSON.
- `GET /analytics/export/csv` — Export lexicon dictionary as CSV.

### ⚡ WebSockets (`/api/v1/ws`)
- `ws://127.0.0.1:8000/api/v1/ws/activity` — Live preservation event broadcast.
- `ws://127.0.0.1:8000/api/v1/ws/dictation/{recording_id}` — Real-time collaborative dictation.
- `ws://127.0.0.1:8000/api/v1/ws/quiz/{deck_id}` — Live multiplayer quiz room.

---

## 📁 Project Structure

```
DIGITAL_PRESERVATION_OF_REGIONAL_LANGUAGE_AND_DIALECTS/
├── app/
│   ├── api/             # REST API routers & WebSocket handlers
│   ├── models/          # SQLAlchemy ORM database models
│   ├── schemas/         # Pydantic validation DTOs & OpenAPI schemas
│   ├── services/        # Phonetic, Audio, Auth, WS Manager, & Seed data
│   ├── config.py        # Environment & App settings
│   ├── database.py      # Database engine setup
│   └── main.py          # FastAPI Application entrypoint
├── uploads/             # Audio recordings & transcript files storage
├── tests/               # Pytest unit & integration test suite
├── run_server.py        # Interactive server runner script
├── requirements.txt     # Python package dependencies
└── README.md            # Backend Documentation
```

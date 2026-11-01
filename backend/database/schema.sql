-- =================================================================
-- BhashaLok — Marathi Language & Regional Dialect Repository Schema
-- Database: SQLite 3 / PostgreSQL Compatible DDL
-- =================================================================

-- 1. Users & Authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role VARCHAR(50) DEFAULT 'Contributor',
    reputation_points INTEGER DEFAULT 0,
    badge_title VARCHAR(100) DEFAULT 'Preservation Enthusiast',
    bio TEXT,
    location VARCHAR(100),
    district VARCHAR(100),
    profile_image VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- 2. Language Varieties & Regional Dialects
CREATE TABLE IF NOT EXISTS languages_varieties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    region VARCHAR(100),
    code VARCHAR(20) UNIQUE,
    parent_language VARCHAR(100) DEFAULT 'Marathi',
    region_name VARCHAR(100),
    state VARCHAR(100) DEFAULT 'Maharashtra',
    districts VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    endangerment_status VARCHAR(50) DEFAULT 'Vulnerable',
    estimated_speakers INTEGER DEFAULT 50000,
    cultural_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_languages_varieties_name ON languages_varieties(name);
CREATE INDEX IF NOT EXISTS ix_languages_varieties_code ON languages_varieties(code);

-- 3. Semantic Categories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- 4. Field Contributors & Researchers
CREATE TABLE IF NOT EXISTS contributors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    district VARCHAR(100),
    role VARCHAR(100),
    bio TEXT,
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Vocabulary Entries (Lexicon Vault)
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(150) NOT NULL,
    transliteration VARCHAR(150),
    meaning TEXT NOT NULL,
    meaning_standard_lang TEXT,
    language VARCHAR(50) DEFAULT 'Marathi',
    variety VARCHAR(100) DEFAULT 'Standard Marathi',
    dialect_id INTEGER,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    district VARCHAR(100),
    taluka VARCHAR(100),
    example_sentence TEXT,
    example_sentence_translation TEXT,
    ipa_transcription VARCHAR(150),
    phonetic_code VARCHAR(100),
    part_of_speech VARCHAR(50) DEFAULT 'Noun',
    etymology TEXT,
    pronunciation VARCHAR(150),
    audio_url VARCHAR(255),
    contributor_id INTEGER,
    submitted_by_id INTEGER,
    verified_by_id INTEGER,
    source VARCHAR(100) DEFAULT 'Survey Data',
    status VARCHAR(50) DEFAULT 'published',
    verification_status VARCHAR(50) DEFAULT 'Verified',
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dialect_id) REFERENCES languages_varieties(id) ON DELETE SET NULL,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id) ON DELETE SET NULL,
    FOREIGN KEY (submitted_by_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (verified_by_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_entries_word ON entries(word);
CREATE INDEX IF NOT EXISTS ix_entries_category ON entries(category);
CREATE INDEX IF NOT EXISTS ix_entries_variety ON entries(variety);
CREATE INDEX IF NOT EXISTS ix_entries_district ON entries(district);

-- 6. Voice Recordings & Audio Archive
CREATE TABLE IF NOT EXISTS voice_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER,
    contributor_id INTEGER,
    dialect_id INTEGER,
    submitted_by_id INTEGER,
    audio_file VARCHAR(255) NOT NULL,
    title VARCHAR(200),
    genre VARCHAR(100) DEFAULT 'Culture',
    speaker_name VARCHAR(100),
    speaker_age INTEGER,
    speaker_gender VARCHAR(20),
    locality VARCHAR(150),
    duration FLOAT DEFAULT 0.0,
    waveform_json TEXT,
    language VARCHAR(50) DEFAULT 'Marathi',
    variety VARCHAR(100),
    region VARCHAR(100),
    transcript TEXT,
    transcript_translation_en TEXT,
    transcript_translation_standard TEXT,
    srt_subtitles TEXT,
    verification_status VARCHAR(50) DEFAULT 'Verified',
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id) ON DELETE SET NULL,
    FOREIGN KEY (dialect_id) REFERENCES languages_varieties(id) ON DELETE SET NULL,
    FOREIGN KEY (submitted_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 7. Peer Verification Votes
CREATE TABLE IF NOT EXISTS lexicon_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lexicon_id INTEGER NOT NULL,
    vote INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (lexicon_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- 8. Interactive Quiz Decks
CREATE TABLE IF NOT EXISTS quiz_decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dialect_id INTEGER,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50) DEFAULT 'Beginner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dialect_id) REFERENCES languages_varieties(id) ON DELETE SET NULL
);

-- 9. Quiz Questions
CREATE TABLE IF NOT EXISTS quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    correct_option VARCHAR(1) NOT NULL,
    explanation TEXT,
    FOREIGN KEY (deck_id) REFERENCES quiz_decks(id) ON DELETE CASCADE
);

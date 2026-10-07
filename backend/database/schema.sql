-- Schema for BhashaLok Marathi Language & Regional Dialect Repository

CREATE TABLE IF NOT EXISTS languages_varieties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    region VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

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

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(150) NOT NULL,
    transliteration VARCHAR(150),
    meaning TEXT NOT NULL,
    language VARCHAR(50) DEFAULT 'Marathi',
    variety VARCHAR(100) DEFAULT 'Standard Marathi',
    category VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    district VARCHAR(100),
    taluka VARCHAR(100),
    example_sentence TEXT,
    pronunciation VARCHAR(150),
    audio_url VARCHAR(255),
    contributor_id INTEGER,
    source VARCHAR(100) DEFAULT 'Survey Data',
    status VARCHAR(50) DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS voice_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER,
    contributor_id INTEGER,
    audio_file VARCHAR(255) NOT NULL,
    duration FLOAT DEFAULT 0.0,
    language VARCHAR(50) DEFAULT 'Marathi',
    variety VARCHAR(100),
    region VARCHAR(100),
    transcript TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id) ON DELETE SET NULL
);

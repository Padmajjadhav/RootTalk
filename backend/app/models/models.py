import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    LINGUIST = "Linguist"
    CONTRIBUTOR = "Contributor"

class EndangermentStatus(str, enum.Enum):
    SAFE = "Safe"
    VULNERABLE = "Vulnerable"
    DEFINITELY_ENDANGERED = "Definitely Endangered"
    SEVERELY_ENDANGERED = "Severely Endangered"
    CRITICALLY_ENDANGERED = "Critically Endangered"
    EXTINCT = "Extinct"

class VerificationStatus(str, enum.Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default=UserRole.CONTRIBUTOR)
    reputation_points = Column(Integer, default=10)
    badge_title = Column(String(50), default="Linguistic Enthusiast")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lexicon_entries = relationship("LexiconEntry", back_populates="submitted_by", foreign_keys="LexiconEntry.submitted_by_id")
    audio_archives = relationship("AudioArchive", back_populates="submitted_by")

class Dialect(Base):
    __tablename__ = "dialects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False) # e.g. Malvani
    parent_language = Column(String(100), index=True, nullable=False) # e.g. Marathi
    code = Column(String(20), unique=True, index=True, nullable=False) # e.g. mar-mal
    region_name = Column(String(100), nullable=False) # e.g. Konkan Region
    state = Column(String(100), nullable=False) # e.g. Maharashtra
    districts = Column(String(255), nullable=True) # e.g. Sindhudurg, Ratnagiri
    latitude = Column(Float, nullable=True) # 16.0000
    longitude = Column(Float, nullable=True) # 73.5000
    endangerment_status = Column(String(30), default=EndangermentStatus.VULNERABLE)
    estimated_speakers = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    cultural_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lexicon_entries = relationship("LexiconEntry", back_populates="dialect", cascade="all, delete-orphan")
    audio_archives = relationship("AudioArchive", back_populates="dialect", cascade="all, delete-orphan")
    quizzes = relationship("QuizDeck", back_populates="dialect", cascade="all, delete-orphan")

class LexiconEntry(Base):
    __tablename__ = "lexicon_entries"

    id = Column(Integer, primary_key=True, index=True)
    dialect_id = Column(Integer, ForeignKey("dialects.id"), nullable=False)
    term = Column(String(150), index=True, nullable=False) # Dialect Word/Phrase
    script = Column(String(50), default="Devanagari")
    ipa_transcription = Column(String(150), nullable=True) # International Phonetic Alphabet
    phonetic_code = Column(String(100), index=True, nullable=True) # Phonetic indexing key
    meaning_en = Column(Text, nullable=False)
    meaning_standard_lang = Column(Text, nullable=False) # Standard Marathi / Hindi translation
    part_of_speech = Column(String(50), nullable=True) # Noun, Verb, Idiom, etc.
    example_sentence_dialect = Column(Text, nullable=True)
    example_sentence_translation = Column(Text, nullable=True)
    etymology = Column(Text, nullable=True)
    semantic_category = Column(String(50), index=True, default="Daily Life") # Folklore, Agriculture, Maritime, etc.
    audio_sample_url = Column(String(255), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_status = Column(String(20), default=VerificationStatus.PENDING)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dialect = relationship("Dialect", back_populates="lexicon_entries")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id], back_populates="lexicon_entries")

class AudioArchive(Base):
    __tablename__ = "audio_archives"

    id = Column(Integer, primary_key=True, index=True)
    dialect_id = Column(Integer, ForeignKey("dialects.id"), nullable=False)
    title = Column(String(200), index=True, nullable=False)
    genre = Column(String(50), index=True, nullable=False) # Folk Tale, Ovi, Oral History, Proverb
    speaker_name = Column(String(100), nullable=True)
    speaker_age = Column(Integer, nullable=True)
    speaker_gender = Column(String(20), nullable=True)
    locality = Column(String(100), nullable=True)
    audio_file_path = Column(String(255), nullable=False)
    duration_seconds = Column(Float, default=0.0)
    waveform_json = Column(Text, nullable=True) # Normalized amplitude peaks for backend waveform visualization
    transcript_text = Column(Text, nullable=True) # Original dialect transcript
    transcript_translation_en = Column(Text, nullable=True)
    transcript_translation_standard = Column(Text, nullable=True)
    srt_subtitles = Column(Text, nullable=True) # Generated Subtitle file content
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_status = Column(String(20), default=VerificationStatus.PENDING)
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dialect = relationship("Dialect", back_populates="audio_archives")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id], back_populates="audio_archives")

class LexiconVote(Base):
    __tablename__ = "lexicon_votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lexicon_id = Column(Integer, ForeignKey("lexicon_entries.id"), nullable=False)
    vote = Column(Integer, nullable=False) # +1 or -1
    comment = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class QuizDeck(Base):
    __tablename__ = "quiz_decks"

    id = Column(Integer, primary_key=True, index=True)
    dialect_id = Column(Integer, ForeignKey("dialects.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(30), default="Beginner") # Beginner, Intermediate, Expert
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dialect = relationship("Dialect", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="deck", cascade="all, delete-orphan")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("quiz_decks.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(200), nullable=False)
    option_b = Column(String(200), nullable=False)
    option_c = Column(String(200), nullable=False)
    option_d = Column(String(200), nullable=False)
    correct_option = Column(String(1), nullable=False) # 'A', 'B', 'C', or 'D'
    explanation = Column(Text, nullable=True)

    deck = relationship("QuizDeck", back_populates="questions")

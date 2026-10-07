import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    LINGUIST = "Linguist"
    CONTRIBUTOR = "Contributor"
    LISTENER = "Listener"

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
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(String(50), default="Contributor")
    reputation_points = Column(Integer, default=0)
    badge_title = Column(String(100), default="Preservation Enthusiast")
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    profile_image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LanguageVariety(Base):
    __tablename__ = "languages_varieties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    region = Column(String(100), nullable=True)
    code = Column(String(20), unique=True, index=True, nullable=True)
    parent_language = Column(String(100), default="Marathi")
    region_name = Column(String(100), nullable=True)
    state = Column(String(100), default="Maharashtra")
    districts = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    endangerment_status = Column(String(50), default="Vulnerable")
    estimated_speakers = Column(Integer, default=50000)
    cultural_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    entries = relationship("Entry", back_populates="dialect")
    audio_archives = relationship("VoiceRecording", back_populates="dialect")

Dialect = LanguageVariety

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

class Contributor(Base):
    __tablename__ = "contributors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    profile_image = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    entries = relationship("Entry", back_populates="contributor")
    voice_recordings = relationship("VoiceRecording", back_populates="contributor")

class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(150), index=True, nullable=False)
    transliteration = Column(String(150), nullable=True)
    meaning = Column(Text, nullable=False)
    meaning_standard_lang = Column(Text, nullable=True)
    language = Column(String(50), default="Marathi")
    variety = Column(String(100), index=True, default="Standard Marathi")
    dialect_id = Column(Integer, ForeignKey("languages_varieties.id"), nullable=True)
    category = Column(String(100), index=True, nullable=False)
    region = Column(String(100), index=True, nullable=True)
    district = Column(String(100), index=True, nullable=True)
    taluka = Column(String(100), nullable=True)
    example_sentence = Column(Text, nullable=True)
    example_sentence_translation = Column(Text, nullable=True)
    ipa_transcription = Column(String(150), nullable=True)
    phonetic_code = Column(String(100), nullable=True)
    part_of_speech = Column(String(50), default="Noun")
    etymology = Column(Text, nullable=True)
    pronunciation = Column(String(150), nullable=True)
    audio_url = Column(String(255), nullable=True)
    contributor_id = Column(Integer, ForeignKey("contributors.id"), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source = Column(String(100), default="Survey Data")
    status = Column(String(50), default="published")
    verification_status = Column(String(50), default="Verified")
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    dialect = relationship("LanguageVariety", back_populates="entries")
    contributor = relationship("Contributor", back_populates="entries")
    voice_recordings = relationship("VoiceRecording", back_populates="entry", cascade="all, delete-orphan")

    @property
    def term(self):
        return self.word

    @term.setter
    def term(self, value):
        self.word = value

    @property
    def script(self):
        return self.transliteration or "Devanagari"

    @script.setter
    def script(self, value):
        self.transliteration = value

    @property
    def meaning_en(self):
        return self.meaning

    @meaning_en.setter
    def meaning_en(self, value):
        self.meaning = value

    @property
    def semantic_category(self):
        return self.category

    @semantic_category.setter
    def semantic_category(self, value):
        self.category = value

    @property
    def example_sentence_dialect(self):
        return self.example_sentence

    @example_sentence_dialect.setter
    def example_sentence_dialect(self, value):
        self.example_sentence = value

    @property
    def audio_sample_url(self):
        return self.audio_url

    @audio_sample_url.setter
    def audio_sample_url(self, value):
        self.audio_url = value

LexiconEntry = Entry

class VoiceRecording(Base):
    __tablename__ = "voice_recordings"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=True)
    contributor_id = Column(Integer, ForeignKey("contributors.id"), nullable=True)
    dialect_id = Column(Integer, ForeignKey("languages_varieties.id"), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    audio_file = Column(String(255), nullable=False)
    title = Column(String(200), nullable=True)
    genre = Column(String(100), default="Culture")
    speaker_name = Column(String(100), nullable=True)
    speaker_age = Column(Integer, nullable=True)
    speaker_gender = Column(String(20), nullable=True)
    locality = Column(String(150), nullable=True)
    duration = Column(Float, default=0.0)
    waveform_json = Column(Text, nullable=True)
    language = Column(String(50), default="Marathi")
    variety = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    transcript = Column(Text, nullable=True)
    transcript_translation_en = Column(Text, nullable=True)
    transcript_translation_standard = Column(Text, nullable=True)
    srt_subtitles = Column(Text, nullable=True)
    verification_status = Column(String(50), default="Verified")
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    entry = relationship("Entry", back_populates="voice_recordings")
    contributor = relationship("Contributor", back_populates="voice_recordings")
    dialect = relationship("LanguageVariety", back_populates="audio_archives")

    @property
    def audio_file_path(self):
        return self.audio_file

    @audio_file_path.setter
    def audio_file_path(self, value):
        self.audio_file = value

    @property
    def duration_seconds(self):
        return self.duration

    @duration_seconds.setter
    def duration_seconds(self, value):
        self.duration = value

    @property
    def transcript_text(self):
        return self.transcript

    @transcript_text.setter
    def transcript_text(self, value):
        self.transcript = value

AudioArchive = VoiceRecording

class LexiconVote(Base):
    __tablename__ = "lexicon_votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lexicon_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    vote = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class QuizDeck(Base):
    __tablename__ = "quiz_decks"

    id = Column(Integer, primary_key=True, index=True)
    dialect_id = Column(Integer, ForeignKey("languages_varieties.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(50), default="Beginner")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    questions = relationship("QuizQuestion", back_populates="deck", cascade="all, delete-orphan")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("quiz_decks.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_option = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=True)

    deck = relationship("QuizDeck", back_populates="questions")

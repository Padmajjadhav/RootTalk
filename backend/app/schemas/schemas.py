from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
import datetime

# --- AUTH SCHEMAS ---
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "Contributor"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    reputation_points: int = 0
    badge_title: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: bool = True
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

# --- DIALECT / LANGUAGE VARIETY SCHEMAS ---
class DialectCreate(BaseModel):
    name: str
    parent_language: Optional[str] = "Marathi"
    code: Optional[str] = None
    region_name: Optional[str] = None
    state: Optional[str] = "Maharashtra"
    districts: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    endangerment_status: Optional[str] = "Vulnerable"
    estimated_speakers: Optional[int] = 50000
    description: Optional[str] = None
    cultural_notes: Optional[str] = None

class DialectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    endangerment_status: Optional[str] = None
    estimated_speakers: Optional[int] = None
    cultural_notes: Optional[str] = None

class DialectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    region_name: Optional[str] = None
    region: Optional[str] = None
    parent_language: Optional[str] = "Marathi"
    code: Optional[str] = None
    state: Optional[str] = "Maharashtra"
    districts: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    endangerment_status: Optional[str] = "Vulnerable"
    estimated_speakers: Optional[int] = 50000
    lexicon_count: Optional[int] = 0
    audio_count: Optional[int] = 0
    preservation_score: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)

LanguageVarietyResponse = DialectResponse

# --- CATEGORY & CONTRIBUTOR SCHEMAS ---
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ContributorResponse(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    district: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- ENTRY / LEXICON SCHEMAS ---
class LexiconCreate(BaseModel):
    dialect_id: Optional[int] = 1
    term: str
    script: Optional[str] = "Devanagari"
    ipa_transcription: Optional[str] = None
    meaning_en: str
    meaning_standard_lang: Optional[str] = None
    part_of_speech: Optional[str] = "Noun"
    example_sentence_dialect: Optional[str] = None
    example_sentence_translation: Optional[str] = None
    etymology: Optional[str] = None
    semantic_category: Optional[str] = "General"

class LexiconUpdate(BaseModel):
    term: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_standard_lang: Optional[str] = None
    ipa_transcription: Optional[str] = None
    example_sentence_dialect: Optional[str] = None

class LexiconResponse(BaseModel):
    id: int
    dialect_id: Optional[int] = None
    term: str
    script: Optional[str] = "Devanagari"
    ipa_transcription: Optional[str] = None
    meaning_en: str
    meaning_standard_lang: Optional[str] = None
    part_of_speech: Optional[str] = "Noun"
    example_sentence_dialect: Optional[str] = None
    example_sentence_translation: Optional[str] = None
    etymology: Optional[str] = None
    semantic_category: Optional[str] = "General"
    verification_status: Optional[str] = "Verified"
    upvotes: int = 0
    downvotes: int = 0
    audio_sample_url: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class EntryResponse(BaseModel):
    id: int
    word: str
    transliteration: Optional[str] = None
    meaning: str
    language: str = "Marathi"
    variety: Optional[str] = "Standard Marathi"
    category: str
    region: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    example_sentence: Optional[str] = None
    pronunciation: Optional[str] = None
    audio_url: Optional[str] = None
    contributor_id: Optional[int] = None
    source: Optional[str] = "Survey Data"
    status: Optional[str] = "published"
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class EntryCreate(BaseModel):
    word: str
    transliteration: Optional[str] = None
    meaning: str
    variety: Optional[str] = "Standard Marathi"
    category: str
    region: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    example_sentence: Optional[str] = None
    pronunciation: Optional[str] = None
    contributor_name: Optional[str] = None
    consent: Optional[bool] = True

class PhoneticSearchRequest(BaseModel):
    query_term: str
    dialect_id: Optional[int] = None
    max_distance: int = 3

# --- AUDIO / VOICE RECORDING SCHEMAS ---
class AudioArchiveCreate(BaseModel):
    dialect_id: Optional[int] = 1
    title: str
    genre: Optional[str] = "Oral History"
    speaker_name: Optional[str] = None
    transcript_text: Optional[str] = None

class AudioArchiveResponse(BaseModel):
    id: int
    dialect_id: Optional[int] = None
    title: str
    genre: Optional[str] = "Culture"
    speaker_name: Optional[str] = None
    audio_file_path: str
    duration_seconds: float = 0.0
    waveform_json: Optional[str] = None
    transcript_text: Optional[str] = None
    verification_status: Optional[str] = "Verified"
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class VoiceRecordingResponse(BaseModel):
    id: int
    entry_id: Optional[int] = None
    contributor_id: Optional[int] = None
    audio_file: str
    duration: float = 0.0
    language: str = "Marathi"
    variety: Optional[str] = None
    region: Optional[str] = None
    transcript: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- ANALYTICS & STATS SCHEMAS ---
class PreservationStatsResponse(BaseModel):
    total_dialects: int
    total_words_preserved: int
    total_audio_recordings: int
    total_active_contributors: int
    preservation_coverage_by_status: dict
    top_dialects_by_entries: List[dict]

class StatsResponse(BaseModel):
    totalEntries: int
    totalVarieties: int
    totalContributors: int
    totalVoiceRecordings: int
    totalRegions: int

# --- QUIZ SCHEMAS ---
class QuizQuestionResponse(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    explanation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class QuizDeckResponse(BaseModel):
    id: int
    dialect_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    difficulty: str
    questions: List[QuizQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SingleAnswerPayload(BaseModel):
    question_id: int
    selected_option: str

class QuizSubmissionRequest(BaseModel):
    deck_id: int
    answers: List[SingleAnswerPayload]

QuizSubmitRequest = QuizSubmissionRequest

class QuizResultResponse(BaseModel):
    deck_id: int
    total_questions: int
    correct_count: int
    score_percentage: float
    reputation_earned: int

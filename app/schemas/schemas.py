from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
import datetime

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, json_schema_extra={"example": "rajesh_linguist"})
    email: EmailStr = Field(..., json_schema_extra={"example": "rajesh@preservation.org"})
    full_name: Optional[str] = Field(None, json_schema_extra={"example": "Dr. Rajesh Patil"})
    role: str = Field("Contributor", json_schema_extra={"example": "Linguist"})

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, json_schema_extra={"example": "SecretPass123!"})

class UserLogin(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "rajesh_linguist"})
    password: str = Field(..., json_schema_extra={"example": "SecretPass123!"})

class UserResponse(UserBase):
    id: int
    reputation_points: int
    badge_title: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# --- DIALECT SCHEMAS ---
class DialectBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Malvani"})
    parent_language: str = Field(..., json_schema_extra={"example": "Marathi"})
    code: str = Field(..., json_schema_extra={"example": "mar-mal"})
    region_name: str = Field(..., json_schema_extra={"example": "Konkan Region"})
    state: str = Field(..., json_schema_extra={"example": "Maharashtra"})
    districts: Optional[str] = Field(None, json_schema_extra={"example": "Sindhudurg, Ratnagiri"})
    latitude: Optional[float] = Field(None, json_schema_extra={"example": 16.0000})
    longitude: Optional[float] = Field(None, json_schema_extra={"example": 73.5000})
    endangerment_status: str = Field("Vulnerable", json_schema_extra={"example": "Vulnerable"})
    estimated_speakers: Optional[int] = Field(None, json_schema_extra={"example": 1500000})
    description: Optional[str] = Field(None, json_schema_extra={"example": "A coastal Marathi dialect spoken in Sindhudurg and South Konkan."})
    cultural_notes: Optional[str] = Field(None, json_schema_extra={"example": "Rich in Dashavatara folk theatre, sea lore, and unique coastal terminology."})

class DialectCreate(DialectBase):
    pass

class DialectUpdate(BaseModel):
    name: Optional[str] = None
    endangerment_status: Optional[str] = None
    estimated_speakers: Optional[int] = None
    description: Optional[str] = None
    cultural_notes: Optional[str] = None

class DialectResponse(DialectBase):
    id: int
    created_at: datetime.datetime
    lexicon_count: Optional[int] = 0
    audio_count: Optional[int] = 0
    preservation_score: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)

# --- LEXICON SCHEMAS ---
class LexiconBase(BaseModel):
    term: str = Field(..., json_schema_extra={"example": "काय रे ख़य चाललोस?"})
    script: str = Field("Devanagari", json_schema_extra={"example": "Devanagari"})
    ipa_transcription: Optional[str] = Field(None, json_schema_extra={"example": "/kaːj reː kʰəj t͡saːllos/"})
    meaning_en: str = Field(..., json_schema_extra={"example": "Where are you going?"})
    meaning_standard_lang: str = Field(..., json_schema_extra={"example": "कुठे चालला आहेस?"})
    part_of_speech: Optional[str] = Field(None, json_schema_extra={"example": "Phrase / Expression"})
    example_sentence_dialect: Optional[str] = Field(None, json_schema_extra={"example": "आजु ख़य चाललोस रे तू?"})
    example_sentence_translation: Optional[str] = Field(None, json_schema_extra={"example": "Where are you heading today?"})
    etymology: Optional[str] = Field(None, json_schema_extra={"example": "Derived from Old Konkani/Marathi coastal phonetic shifts."})
    semantic_category: str = Field("Daily Life", json_schema_extra={"example": "Daily Life"})

class LexiconCreate(LexiconBase):
    dialect_id: int = Field(..., json_schema_extra={"example": 1})

class LexiconUpdate(BaseModel):
    term: Optional[str] = None
    ipa_transcription: Optional[str] = None
    meaning_en: Optional[str] = None
    meaning_standard_lang: Optional[str] = None
    verification_status: Optional[str] = None

class LexiconResponse(LexiconBase):
    id: int
    dialect_id: int
    submitted_by_id: Optional[int] = None
    verification_status: str
    verified_by_id: Optional[int] = None
    upvotes: int
    downvotes: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class PhoneticSearchRequest(BaseModel):
    query_term: str = Field(..., json_schema_extra={"example": "khay"})
    dialect_id: Optional[int] = Field(None, json_schema_extra={"example": 1})
    max_distance: int = Field(3, json_schema_extra={"example": 3})

# --- AUDIO ARCHIVE SCHEMAS ---
class AudioArchiveBase(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Ocean Story of Malvan Fishermen"})
    genre: str = Field(..., json_schema_extra={"example": "Folk Tale"})
    speaker_name: Optional[str] = Field(None, json_schema_extra={"example": "Baburao Kadam"})
    speaker_age: Optional[int] = Field(None, json_schema_extra={"example": 68})
    speaker_gender: Optional[str] = Field(None, json_schema_extra={"example": "Male"})
    locality: Optional[str] = Field(None, json_schema_extra={"example": "Malvan Beach"})
    transcript_text: Optional[str] = Field(None, json_schema_extra={"example": "दर्या आज गरम आसा, मासोळी कमी गावतली..."})
    transcript_translation_en: Optional[str] = Field(None, json_schema_extra={"example": "The sea is warm today, we might catch fewer fish..."})
    transcript_translation_standard: Optional[str] = Field(None, json_schema_extra={"example": "समुद्र आज गरम आहे, मासे कमी मिळतील..."})

class AudioArchiveCreate(AudioArchiveBase):
    dialect_id: int

class AudioArchiveResponse(AudioArchiveBase):
    id: int
    dialect_id: int
    audio_file_path: str
    duration_seconds: float
    waveform_json: Optional[str] = None
    verification_status: str
    views_count: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

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
    dialect_id: int
    title: str
    description: Optional[str] = None
    difficulty: str
    questions: List[QuizQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class QuizAnswerSubmit(BaseModel):
    question_id: int
    selected_option: str # 'A', 'B', 'C', 'D'

class QuizSubmitRequest(BaseModel):
    deck_id: int
    answers: List[QuizAnswerSubmit]

class QuizResultResponse(BaseModel):
    deck_id: int
    total_questions: int
    correct_count: int
    score_percentage: float
    reputation_earned: int
    feedback: str

# --- ANALYTICS SCHEMAS ---
class PreservationStatsResponse(BaseModel):
    total_dialects: int
    total_words_preserved: int
    total_audio_recordings: int
    total_active_contributors: int
    preservation_coverage_by_status: dict
    top_dialects_by_entries: List[dict]

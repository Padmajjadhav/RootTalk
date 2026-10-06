from sqlalchemy.orm import Session
from app.models import (
    User, UserRole, EndangermentStatus, VerificationStatus,
    Dialect, LexiconEntry, AudioArchive, QuizDeck, QuizQuestion
)
from app.services.auth_service import get_password_hash
from app.services.phonetic import devanagari_to_ipa, generate_indic_soundex
from app.services.audio_service import generate_waveform_peaks, generate_srt_subtitles
import json

def seed_database(db: Session):
    # Check if database already has dialects seeded
    if db.query(Dialect).first():
        return

    print("Seeding database with rich Regional Languages & Dialects data...")

    # 1. Seed Users
    admin_user = User(
        username="admin",
        email="admin@preservation.org",
        hashed_password=get_password_hash("Admin123!"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        reputation_points=1000,
        badge_title="Grand Preserver"
    )
    linguist_user = User(
        username="dr_patil",
        email="patil@linguistics.ac.in",
        hashed_password=get_password_hash("Linguist123!"),
        full_name="Dr. Rajesh Patil (PhD Linguistics)",
        role=UserRole.LINGUIST,
        reputation_points=500,
        badge_title="Senior Dialectologist"
    )
    contributor_user = User(
        username="konkan_preserver",
        email="suhas@konkan.org",
        hashed_password=get_password_hash("User123!"),
        full_name="Suhas Sawant",
        role=UserRole.CONTRIBUTOR,
        reputation_points=120,
        badge_title="Cultural Explorer"
    )
    db.add_all([admin_user, linguist_user, contributor_user])
    db.commit()

    # 2. Seed Dialects
    malvani = Dialect(
        name="Malvani",
        parent_language="Marathi",
        code="mar-mal",
        region_name="Konkan Coast",
        state="Maharashtra",
        districts="Sindhudurg, Ratnagiri, Goa Border",
        latitude=16.0500,
        longitude=73.4667,
        endangerment_status=EndangermentStatus.VULNERABLE,
        estimated_speakers=1800000,
        description="A vibrant coastal Marathi-Konkani transitional dialect spoken predominantly in the Sindhudurg district of Maharashtra. Famous for distinct sound shifts (e.g. 'c' to 'ch', shortening of vowels) and coastal marine terminology.",
        cultural_notes="Preserves Dashavatara folk theatre scripts, maritime folk songs, fishing terminology, and sea-deity rituals."
    )

    varhadi = Dialect(
        name="Varhadi",
        parent_language="Marathi",
        code="mar-var",
        region_name="Vidarbha",
        state="Maharashtra",
        districts="Amravati, Akola, Buldhana, Yavatmal, Washim, Wardha",
        latitude=20.9333,
        longitude=77.7500,
        endangerment_status=EndangermentStatus.VULNERABLE,
        estimated_speakers=12000000,
        description="Spoken across the Vidarbha region of Maharashtra. Notable for soft pronunciation, distinct verb inflections, and rich agricultural lore.",
        cultural_notes="Home to legendary Marathi saint literature, Bharud folk songs, and cotton-farming community traditions."
    )

    ahirani = Dialect(
        name="Ahirani",
        parent_language="Marathi",
        code="mar-ahi",
        region_name="Khandesh",
        state="Maharashtra",
        districts="Dhule, Jalgaon, Nandurbar, Nashik (North)",
        latitude=20.9000,
        longitude=74.7833,
        endangerment_status=EndangermentStatus.DEFINITELY_ENDANGERED,
        estimated_speakers=3000000,
        description="Spoken in the Khandesh region along the Tapi river basin. Combines ancient Marathi roots with Bhili and Gujarati phonetic influences.",
        cultural_notes="Renowned for 'Kanbai' festival songs, oral storytelling, and unique culinary vocabulary."
    )

    awadhi = Dialect(
        name="Awadhi",
        parent_language="Hindi",
        code="hin-awa",
        region_name="Awadh Region",
        state="Uttar Pradesh",
        districts="Lucknow, Ayodhya, Gonda, Bahraich, Pratapgarh",
        latitude=26.8500,
        longitude=80.9500,
        endangerment_status=EndangermentStatus.VULNERABLE,
        estimated_speakers=38000000,
        description="A prominent Eastern Hindi dialect with immense literary heritage including the epic Ramcharitmanas by Tulsidas.",
        cultural_notes="Famous for classical poetry, folk theater (Nautanki), and refined etiquette vocabulary."
    )

    db.add_all([malvani, varhadi, ahirani, awadhi])
    db.commit()

    # 3. Seed Lexicon Entries
    lexicon_items = [
        # Malvani
        LexiconEntry(
            dialect_id=malvani.id,
            term="ख़य चाललोस?",
            script="Devanagari",
            ipa_transcription="/kʰəj t͡saːlloːs/",
            phonetic_code=generate_indic_soundex("khay challos"),
            meaning_en="Where are you going?",
            meaning_standard_lang="कुठे चालला आहेस?",
            part_of_speech="Phrase",
            example_sentence_dialect="बाबल्या, आजु सकाळीच ख़य चाललोस?",
            example_sentence_translation="Bablya, where are you going so early in the morning?",
            etymology="Proto-Konkani/Marathi coastal shift of 'Kuthe' -> 'Khay'",
            semantic_category="Daily Greetings",
            submitted_by_id=contributor_user.id,
            verification_status=VerificationStatus.VERIFIED,
            verified_by_id=linguist_user.id,
            upvotes=15
        ),
        LexiconEntry(
            dialect_id=malvani.id,
            term="चेडू",
            script="Devanagari",
            ipa_transcription="/t͡ʃeːɖuː/",
            phonetic_code=generate_indic_soundex("chedu"),
            meaning_en="Girl / Young Daughter",
            meaning_standard_lang="मुलगी / कन्‍या",
            part_of_speech="Noun",
            example_sentence_dialect="त्या चेडवान मस्त रांगोळी काढलीया.",
            example_sentence_translation="That girl drew a beautiful rangoli.",
            etymology="Unique coastal Konkan term preserved in Malvani dialect.",
            semantic_category="Family & Society",
            submitted_by_id=contributor_user.id,
            verification_status=VerificationStatus.VERIFIED,
            verified_by_id=linguist_user.id,
            upvotes=24
        ),
        LexiconEntry(
            dialect_id=malvani.id,
            term="येवा कोंकण आपलोच आसा!",
            script="Devanagari",
            ipa_transcription="/jeːʋaː koːŋkəɳ aːpəloːt͡ʃ aːsaː/",
            phonetic_code=generate_indic_soundex("yeva konkan"),
            meaning_en="Welcome! Konkan belongs to all of us!",
            meaning_standard_lang="या, कोकण आपलेच आहे!",
            part_of_speech="Proverb / Idiom",
            example_sentence_dialect="येवा कोंकण आपलोच आसा, म्हाका मासे खाऊक भेटतले!",
            example_sentence_translation="Welcome to Konkan, you will get delicious fish to eat!",
            etymology="Traditional Malvani hospitality greeting.",
            semantic_category="Folklore & Tourism",
            submitted_by_id=contributor_user.id,
            verification_status=VerificationStatus.VERIFIED,
            verified_by_id=linguist_user.id,
            upvotes=40
        ),

        # Varhadi
        LexiconEntry(
            dialect_id=varhadi.id,
            term="कसं काय भाऊ?",
            script="Devanagari",
            ipa_transcription="/kəsəŋ kaːj bʱaːuː/",
            phonetic_code=generate_indic_soundex("kasam kay bhau"),
            meaning_en="How are things going, brother?",
            meaning_standard_lang="कसे काय चालू आहे भावा?",
            part_of_speech="Phrase",
            example_sentence_dialect="अरे रामभाऊ, कसं काय भाऊ? शेतात पेरणी झाली का?",
            example_sentence_translation="Hey Rambhau, how are you brother? Did you finish sowing the farm?",
            etymology="Common Vidarbha friendly inquiry.",
            semantic_category="Daily Greetings",
            submitted_by_id=contributor_user.id,
            verification_status=VerificationStatus.VERIFIED,
            verified_by_id=linguist_user.id,
            upvotes=18
        ),

        # Ahirani
        LexiconEntry(
            dialect_id=ahirani.id,
            term="कशास तुले?",
            script="Devanagari",
            ipa_transcription="/kəʃaːs tuleː/",
            phonetic_code=generate_indic_soundex("kashas tule"),
            meaning_en="Why do you need it / Why are you asking?",
            meaning_standard_lang="तुला कशाला हवे?",
            part_of_speech="Phrase",
            example_sentence_dialect="कशास तुले ते पुस्तक?",
            example_sentence_translation="Why do you need that book?",
            etymology="Khandesh Tapi valley regional expression.",
            semantic_category="Daily Life",
            submitted_by_id=contributor_user.id,
            verification_status=VerificationStatus.VERIFIED,
            verified_by_id=linguist_user.id,
            upvotes=10
        )
    ]
    db.add_all(lexicon_items)
    db.commit()

    # 4. Seed Audio Archives
    malvani_transcript = "दर्या आज उधाणावर आसा. आमचे सगळे कोळी बांधव बोट सावरून किनाऱ्यावर आले. रात्रीचा पाऊस मोठो होतो."
    malvani_srt = generate_srt_subtitles(malvani_transcript, duration_seconds=45.0)
    
    audio_sample = AudioArchive(
        dialect_id=malvani.id,
        title="Sea Story: Tide & Fishermen of Malvan Coast",
        genre="Oral History Interview",
        speaker_name="Fisherman Janardan Bhandari",
        speaker_age=72,
        speaker_gender="Male",
        locality="Malvan Jetty, Sindhudurg",
        audio_file_path="uploads/audio/malvan_sea_story_sample.mp3",
        duration_seconds=45.0,
        waveform_json=json.dumps(generate_waveform_peaks(50)),
        transcript_text=malvani_transcript,
        transcript_translation_en="The ocean has high tides today. All our fellow fishermen secured their boats and came to the shore. Last night's rain was heavy.",
        transcript_translation_standard="समुद्र आज भरतीवर आहे. आमचे सगळे कोळी बांधव बोटी सावरून किनाऱ्यावर आले.",
        srt_subtitles=malvani_srt,
        submitted_by_id=contributor_user.id,
        verification_status=VerificationStatus.VERIFIED,
        views_count=120
    )
    db.add(audio_sample)
    db.commit()

    # 5. Seed Quizzes
    malvani_deck = QuizDeck(
        dialect_id=malvani.id,
        title="Malvani Dialect Vocabulary Challenge",
        description="Test your knowledge of authentic coastal Malvani words, idioms, and daily greetings.",
        difficulty="Beginner"
    )
    db.add(malvani_deck)
    db.commit()

    q1 = QuizQuestion(
        deck_id=malvani_deck.id,
        question_text="What does the Malvani word 'चेडू' (Chedu) mean?",
        option_a="Child / Boy",
        option_b="Girl / Young Daughter",
        option_c="Small Fish",
        option_d="Traditional Wooden Boat",
        correct_option="B",
        explanation="'चेडू' (Chedu) is a classic Malvani term for a girl or daughter."
    )
    q2 = QuizQuestion(
        deck_id=malvani_deck.id,
        question_text="If a Malvani speaker asks 'ख़य चाललोस?', what are they asking?",
        option_a="What time is it?",
        option_b="Where are you going?",
        option_c="What did you eat?",
        option_d="Why are you laughing?",
        correct_option="B",
        explanation="'ख़य' (Khay) means 'Where' and 'चाललोस' (Challos) means 'going'."
    )
    db.add_all([q1, q2])
    db.commit()

    print("Database successfully seeded with dialect preservation repository dataset!")

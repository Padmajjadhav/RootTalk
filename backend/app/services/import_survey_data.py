import csv
import io
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Dialect, LexiconEntry, AudioArchive, User, EndangermentStatus, VerificationStatus
from app.services.phonetic import devanagari_to_ipa, generate_indic_soundex
from app.services.audio_service import generate_waveform_peaks, generate_srt_subtitles

SURVEY_CSV_DATA = """District,Taluka,Village,latitude,longitude,Objective,Instrumental,Ablative,Genitive 1st and 2nd person singular,Genitive 3rd Person singular,Locative Inessive,Present Progressive,Past Progressive,Present Habitual,Past Habitual,Perfective,Ergative case marking on the subject NP in the transitive perfective clause,Verbal agreement in the transitive perfective clause
Ahmednagar,Akole,Brahmanwada,19.343,74.034,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Ahmednagar,Akole,Dongargaon,19.631,74.1,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Ahmednagar,Newasa,Khalal Pimpri,19.575,74.96,[-le],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Akola,Akola,Gopalkhed,20.8747,76.9645,[-la],[-ne],[-un],[-jʰ],[-c],[-t],V-NON.FIN+LAG(AUX),[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Amravati,Amravati,Sawardi,21.017,77.878,,,,,,[-t],,,,[V-t+(hot-AGR)],,Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Auranɡabad,Auranɡabad,Bhikapur-Naiɡaon,19.982,75.329,,,,,,[-t],,,,,,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Beed,Shirur-Kasar,Takalwadi,18.9641,75.4899,,,,[-l],,[-t],,,,,,Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Bhandara,Bhandara,Dhargaon,21.09,79.727,,,,,,[-t],,,,,,"First, second and third person subject NPs are overtly marked with ergative case",Agreement largely with the non-case marked object of the clause and variably with the subject of the clause
Buldhana,Buldhana,Palaskhed Bhat,20.486,76.111,[-la],,,[Noun.oblique],,[-t],[V-t(-AGR)+(AUX)],,,[V-ayc-AGR],,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Chandrapur,Chandrapur,Chaknimbala,20.0351,79.442,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-CP+RAH-AGR+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Dhule,Dhule,Lalinɡ,20.819,74.746,[-le],[-ne],[-un],[-jʰ],[-c],[-t],[V-CP+RAH-AGR+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-Vowel],"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Gadchiroli,Gadchiroli,Khursa-Navegaon,20.24,80.157,[-lə],,,,,[-t],,,,[V-ayc-AGR],,Only third person subject NP is marked overtly with ergative case,Agreement largely with the non-case marked object of the clause and variably with the subject of the clause
Gondia,Gondia,Temni,21.465,80.194,,,,,,[-t],,,,,,Only third person subject NP is marked overtly with ergative case,Agreement largely with the non-case marked object of the clause and variably with the subject of the clause
Hingoli,Hingoli,Karwadi,19.7274,77.1658,[-lə],[-ne],[-un],[-jʰ],[-c],[-t],V-NON.FIN+LAG(AUX),[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Jalna,Jalna,Dhawedi,19.855,75.898,[-lə],,,[Noun.oblique],,[-t],[V-t(-AGR)+(AUX)],,,[V-t+(hot-AGR)],,Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Jalɡaon,Jalɡaon,Dhamanɡaon,21.008,75.56,,,,,,[-t],,,,,,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Kolhapur,Karvir,Gadmudshingi,16.6877,74.2785,[-la],[-ne],[-un],[-jʰ],[-c],,[V-NON.FIN+LAG-AGR+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l],Only third person subject NP is marked overtly with ergative case,Agreement largely with the non-case marked object of the clause and variably with the subject of the clause
Latur,Latur,Pakharsanɡavi,18.397,76.522,[-la],[-ne],[-un],[-jʰ],[-c],[-t],V-NON.FIN+LAG(AUX),[V-(NON.FIN)+LAG+AUX-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement largely with the non-case marked object of the clause and variably with the subject of the clause
Nanded,Nanded,Limbɡaon,19.162,77.225,[-la],[-ne],[-un],[-jʰ],[-c],[-t],V-NON.FIN+LAG(AUX),,[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Nandurbar,Nandurbar,Ghotane,21.3389,74.4133,[-le],[-ne],[-un],[-jʰ],[-c],[-t],[V-CP+RAH-AGR+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-Vowel.AGR],[-Vowel],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Nashik,Malegaon,Kalwadi,20.5545,74.7503,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-CP+RAH-AGR+(AUX)],[V-CP+RAH(-AGR)+AUX-AGR],[V-t-AGR],[V-Vowel.AGR],[-Vowel],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Naɡpur,Naɡpur,Yerla,21.2019,78.8983,[-le],[-ne],[-un],[-jʰ],[-c],[-t],[V-CP+RAH-AGR+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Osmanabad,Osmanabad,Shinɡoli,18.236,76.033,,,,,,[-t],,,,,,Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Palɡhar,Vasai,Waɡholi,19.416,72.7607,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Parbhani,Palam,Kapsi,19.0097,76.8611,,,,,,[-t],[V-t(-AGR)+(AUX)],,,[V-t+(hot-AGR)],,Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Pune,Haveli,Jambhli,18.457,73.85,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],,[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Raiɡad,Karjat,Gaulwadi,18.969,73.3444,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Ratnagiri,Ratnagiri,Malgund,17.1661,73.2626,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Sangli,Miraj,Soni,16.9537,74.6873,[-la],[-ne],[-un],[-jʰ],[-c],[-t],V-NON.FIN+LAG(AUX),[V-(NON.FIN)+LAG+AUX-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Satara,Khatav,Mandave,17.556,73.977,[-la],[-ne],[-un],[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],[V-t+hot-AGR],[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Sindhudurɡ,Dodamarɡ,Ayee,15.6287,74.0032,[-ka],[-ne],,[-jʰ],[-c],[-t],[V-t(-AGR)+(AUX)],,[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Solapur,Solapur,Ranmasle,17.842,75.795,[-la],[-ne],[-un],[-jʰ],[-c],[-t],V-NON.FIN+LAG(AUX),,[V-t-AGR],[V-ayc-AGR],[-l-],Only third person subject NP is marked overtly with ergative case,Agreement only with the non-case marked object
Thane,Ambernath,Usatane,19.1204,73.1243,,,,,,[-t],,,,[V-t+(hot-AGR)],,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Wardha,Ashti,Khadka,21.17,78.14,[-le],,,[Noun.oblique],,[-t],[V-t(-AGR)+(AUX)],,,[V-t+(hot-AGR)],,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Washim,Risod,Chakoli,19.9438,76.665,,,,h,,[-t],,,,,,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
Yavatmal,Ghatanji,Khapri,20.157,78.267,[-la],,,[Noun.oblique],,[-t],[V-t(-AGR)+(AUX)],,,[V-Vowel.AGR],,"First, second and third person subject NPs are overtly marked with ergative case",Agreement only with the non-case marked object
"""

AUDIO_STORIES_DATA = [
    ("Ahmednagar", "Akole", "Brahmanwada", 19.343, 74.034, "F30, Class 12, Maratha", "https://sdml.ac.in/story/Brahmanwada/1/fullstory.wav", "Old Woman and the Pumpkin"),
    ("Ahmednagar", "Akole", "Brahmanwada", 19.343, 74.034, "M50, Class 3, Hindu Mahadev Koli", "https://sdml.ac.in/story/Brahmanwada/2/fullstory.wav", "Rabbit and Tortoise"),
    ("Ahmednagar", "Akole", "Dongargaon", 19.631, 74.1, "F60+, Class 2, Maratha", "https://sdml.ac.in/story/Dongargaon/4/fullstory.wav", "The tiger and the goat"),
    ("Amravati", "Warud", "Gadegaon", 21.361, 78.256, "M80, Illiterate, Buddhist Old Mahar", "https://sdml.ac.in/story/Gadegaon/2/fullstory.wav", "About self"),
    ("Aurangabad", "Paithan", "Telwadi", 19.45, 75.369, "M71, Class 10, Hindu Maratha", "https://sdml.ac.in/story/Telwadi/1/fullstory.wav", "Old woman and the pumpkin"),
    ("Beed", "Ambajogai", "Daradwadi", 18.753, 76.6936, "F70, Illiterate, Vanjari", "https://sdml.ac.in/story/Daradwadi/1/fullstory.wav", "The story of Ramayan"),
    ("Chandrapur", "Rajura", "Koshtala-Kolamghotta", 19.587, 79.364, "M27/M35, Class 6, Kolam", "https://sdml.ac.in/story/Koshtala/1/fullstory.wav", "Rabbit and Tortoise (Kolami dialect)"),
    ("Dhule", "Shirpur", "Ambe", 21.429, 75.113, "F55, Class 5, Mali", "https://sdml.ac.in/story/Ambe/1/fullstory.wav", "Old woman and the pumpkin"),
    ("Gadchiroli", "Gadchiroli", "Khursa-Navegaon", 20.24, 80.157, "M61, Illiterate, Khaire Kunbi", "https://sdml.ac.in/story/Khursa/1/fullstory.wav", "The fox and the tiger"),
    ("Gondia", "Sadak Arjuni", "Duggipar", 21.077, 80.166, "M55, Class 9, Hindu Kohli", "https://sdml.ac.in/story/Duggipar/1/fullstory.wav", "The old woman and the fox"),
    ("Kolhapur", "Karvir", "Khupire", 16.7105, 74.145, "M81, Class 3, Harijan", "https://sdml.ac.in/story/Khupire/1/fullstory.wav", "A biographical sketch"),
    ("Latur", "Nilanga", "Dadgi", 18.072, 76.76, "F80, Illiterate, Mahadev Koli", "https://sdml.ac.in/story/Dadɡi/1/fullstory.wav", "A mythological story"),
    ("Nanded", "Kinwat", "Maregaon Khalche", 19.659, 78.115, "M48, Class 9, Andh", "https://sdml.ac.in/story/Mareɡaon (Khalche)/1/fullstory.wav", "Rabbit and Tortoise"),
    ("Nashik", "Surgana", "Surgana", 20.5587, 73.633, "M36, Graduate, Hindu Kokna", "https://sdml.ac.in/story/Surɡana/1/fullstory.wav", "Memories of a college camp"),
    ("Palghar", "Dahanu", "Bordi", 20.0998, 72.73, "M54, Class 11, Somvansi Kshatriya", "https://sdml.ac.in/story/Bordi/1/fullstory.wav", "The cap-seller and the monkeys"),
    ("Pune", "Indapur", "Saradewadi", 18.097, 75.081, "F55, Class 6, Dhangar", "https://sdml.ac.in/story/Saradewadi/1/fullstory.wav", "Old woman and the pumpkin"),
    ("Raigad", "Alibag", "Mandwa", 18.7953, 72.892, "F51, Class 2, Koli", "https://sdml.ac.in/story/Mandwa/1/fullstory.wav", "Life in the coastal village"),
    ("Ratnagiri", "Ratnagiri", "Malgund", 17.1661, 73.2626, "M44, Graduate, Hindu Kunbi", "https://sdml.ac.in/story/Malgund/1/fullstory.wav", "Rabbit and Tortoise"),
    ("Sangli", "Shirala", "Pachumbri", 17.097, 74.118, "M65, Class 9, Maratha", "https://sdml.ac.in/story/Pachumbri/1/fullstory.wav", "About drama & theatre"),
    ("Satara", "Patan", "Helwak", 17.373, 73.722, "F51, Class 7, Nhavi", "https://sdml.ac.in/story/Helwak/2/fullstory.wav", "An Earthquake story"),
    ("Sindhudurg", "Malwan", "Katta", 16.147, 73.536, "F50, Class 7, Hindu Bhandari", "https://sdml.ac.in/story/Katta/1/fullstory.wav", "Rabbit and Tortoise (Malvani Coast)"),
    ("Sindhudurg", "Malwan", "Dandi", 16.0514, 73.4592, "M35, Graduate, Hindu Gabit", "https://sdml.ac.in/story/Dandi/2/fullstory.wav", "About Fisherman Occupation"),
    ("Solapur", "Akkalkot", "Karjal", 17.566, 76.114, "M52, Class 4, Hindu Chambhar", "https://sdml.ac.in/story/Karjal/1/fullstory.wav", "About one's occupation"),
    ("Thane", "Bhiwandi", "Khoni", 19.309, 73.053, "F72, Illiterate, Hindu Mahadev Koli", "https://sdml.ac.in/story/Khoni/1/fullstory.wav", "About one's childhood"),
    ("Wardha", "Ashti", "Thar", 21.203, 78.195, "F23, Graduate, Hindu Gawli OBC", "https://sdml.ac.in/story/Thar/1/fullstory.wav", "About oral literature"),
    ("Washim", "Risod", "Ghonsar", 19.9434, 76.8075, "F60, Class 4, Andh", "https://sdml.ac.in/story/Ghonsar/1/fullstory.wav", "The sparrow and the crow"),
    ("Yavatmal", "Ghatanji", "Khapri", 20.157, 78.267, "F70, Illiterate, Gond", "https://sdml.ac.in/story/Khapri/2/fullstory.wav", "About the wedding ceremony")
]

def import_survey_dataset(db: Session):
    print("Importing Marathi Dialects Survey Dataset into DB...")

    # 1. Parse CSV and Add Dialects
    f = io.StringIO(SURVEY_CSV_DATA.strip())
    reader = csv.DictReader(f)
    
    district_count = 0
    audio_count = 0

    for row in reader:
        district = row.get("District", "").strip()
        taluka = row.get("Taluka", "").strip()
        village = row.get("Village", "").strip()
        lat_str = row.get("latitude", "").strip()
        lon_str = row.get("longitude", "").strip()

        if not district or not village:
            continue

        try:
            lat = float(lat_str) if lat_str else 19.5000
            lon = float(lon_str) if lon_str else 75.5000
        except ValueError:
            lat, lon = 19.5000, 75.5000

        code = f"mar-{district.lower()[:3]}-{village.lower()[:3]}".replace(" ", "")

        existing_d = db.query(Dialect).filter(Dialect.code == code).first()
        if not existing_d:
            dialect = Dialect(
                name=f"{district} ({village})",
                parent_language="Marathi",
                code=code,
                region_name=f"{taluka} Taluka",
                state="Maharashtra",
                districts=district,
                latitude=lat,
                longitude=lon,
                endangerment_status=EndangermentStatus.VULNERABLE,
                estimated_speakers=250000,
                description=f"Preserved Marathi dialect surveyed in {village} village, {taluka} taluka, {district} district.",
                cultural_notes=f"Linguistic features: Objective case [{row.get('Objective', '')}], Instrumental [{row.get('Instrumental', '')}], Ablative [{row.get('Ablative', '')}]."
            )
            db.add(dialect)
            db.commit()
            db.refresh(dialect)
            district_count += 1

    # 2. Add Audio Archive Stories
    sample_admin = db.query(User).first()
    admin_id = sample_admin.id if sample_admin else 1

    for item in AUDIO_STORIES_DATA:
        district, taluka, village, lat, lon, speaker, url, title = item
        code = f"mar-{district.lower()[:3]}-{village.lower()[:3]}".replace(" ", "")
        
        dialect = db.query(Dialect).filter(Dialect.code == code).first()
        if not dialect:
            dialect = db.query(Dialect).first()

        existing_audio = db.query(AudioArchive).filter(AudioArchive.title == title, AudioArchive.locality == village).first()
        if not existing_audio and dialect:
            audio = AudioArchive(
                dialect_id=dialect.id,
                title=title,
                genre="Oral History Story",
                speaker_name=speaker.split(",")[0] if "," in speaker else speaker,
                locality=f"{village}, {district}",
                audio_file_path=url,
                duration_seconds=120.0,
                waveform_json=json.dumps(generate_waveform_peaks(50)),
                transcript_text=f"Preserved oral story '{title}' recorded in {village}, {district}.",
                transcript_translation_en=f"English translation of {title} recorded by {speaker}.",
                transcript_translation_standard=f"{title} - मराठी भाषा बोली संकलन.",
                srt_subtitles=generate_srt_subtitles(f"Preserved oral story {title}", 120.0),
                submitted_by_id=admin_id,
                verification_status=VerificationStatus.VERIFIED,
                views_count=85
            )
            db.add(audio)
            db.commit()
            audio_count += 1

    print(f"Successfully imported {district_count} new regional Marathi dialect survey locations and {audio_count} oral audio recordings into database!")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    import_survey_dataset(db)
    db.close()

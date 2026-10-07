import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import openpyxl
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Entry, LanguageVariety, Category, Contributor

DISTRICT_REGION_MAP = {
    "Sindhudurg": ("Konkan Coast", "Malvani"),
    "Ratnagiri": ("Konkan Coast", "Malvani / Konkani"),
    "Raigad": ("Konkan Coast", "Agri / Koli / Konkani"),
    "Thane": ("Konkan Coast", "Agri / Koli"),
    "Palghar": ("Konkan Coast", "Warli / Agri"),
    "Amravati": ("Vidarbha", "Varhadi"),
    "Akola": ("Vidarbha", "Varhadi"),
    "Buldhana": ("Vidarbha", "Varhadi"),
    "Yavatmal": ("Vidarbha", "Varhadi"),
    "Washim": ("Vidarbha", "Varhadi"),
    "Wardha": ("Vidarbha", "Varhadi"),
    "Nagpur": ("Vidarbha", "Nagpuri / Varhadi"),
    "Dhule": ("Khandesh", "Ahirani"),
    "Jalgaon": ("Khandesh", "Ahirani"),
    "Nandurbar": ("Khandesh", "Ahirani"),
    "Ahmednagar": ("Western Maharashtra", "Deshi Marathi"),
    "Pune": ("Western Maharashtra", "Puneri Marathi"),
    "Satara": ("Western Maharashtra", "Deshi Marathi"),
    "Sangli": ("Western Maharashtra", "Deshi Marathi"),
    "Kolhapur": ("Western Maharashtra", "Kolhapuri Marathi"),
    "Aurangabad": ("Marathwada", "Marathwadi"),
    "Chhatrapati Sambhajinagar": ("Marathwada", "Marathwadi"),
    "Nanded": ("Marathwada", "Marathwadi"),
    "Latur": ("Marathwada", "Marathwadi"),
    "Beed": ("Marathwada", "Marathwadi"),
    "Dharashiv": ("Marathwada", "Marathwadi"),
    "Osmanabad": ("Marathwada", "Marathwadi"),
}

def import_excel_file(file_path: str, db: Session):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return

    print(f"[INFO] Opening Excel file: {file_path}")
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        print("[ERROR] Sheet is empty.")
        return

    # Header Row Detection
    header_idx = 0
    if len(rows) > 1 and ("survey" in str(rows[0][0] or "").lower() or rows[0][1] is None):
        header_idx = 1

    headers = [str(c).strip() if c is not None else "" for c in rows[header_idx]]
    data_rows = rows[header_idx + 1:]

    print(f"[INFO] Using Row {header_idx + 1} as Table Headers ({len(headers)} columns)")

    rows_read = 0
    imported = 0
    duplicates = 0
    invalid = 0

    # Determine if it's a survey file or standard dictionary file
    col_map = {h.lower(): idx for idx, h in enumerate(headers)}
    
    is_survey = "district" in col_map or "village" in col_map

    for row in data_rows:
        rows_read += 1
        if not any(row):
            continue

        if is_survey:
            district_val = str(row[col_map["district"]]).strip() if "district" in col_map and row[col_map["district"]] else "Maharashtra"
            taluka_val = str(row[col_map["taluka"]]).strip() if "taluka" in col_map and row[col_map["taluka"]] else None
            village_val = str(row[col_map["village"]]).strip() if "village" in col_map and row[col_map["village"]] else None

            region, variety = DISTRICT_REGION_MAP.get(district_val, ("Maharashtra", "Regional Marathi"))

            # Iterate through grammatical/feature columns
            for col_name, idx in col_map.items():
                if col_name in ["district", "taluka", "village", "latitude", "longitude", "speaker details"]:
                    continue
                cell_val = row[idx]
                if cell_val is None or str(cell_val).strip() == "":
                    continue

                feature_str = str(cell_val).strip()
                feature_title = headers[idx]

                # Check duplicate
                existing = db.query(Entry).filter(
                    Entry.word == feature_str,
                    Entry.district == district_val,
                    Entry.meaning == f"{feature_title} inflection in {village_val or district_val}"
                ).first()

                if existing:
                    duplicates += 1
                    continue

                example = f"Recorded in {village_val + ', ' if village_val else ''}{taluka_val + ', ' if taluka_val else ''}{district_val} district."

                entry = Entry(
                    word=feature_str,
                    meaning=f"{feature_title} regional expression",
                    meaning_standard_lang=f"{feature_title} (स्थानिक भाषाप्रयोग)",
                    variety=variety,
                    category="Grammar & Regional Dialects",
                    region=region,
                    district=district_val,
                    taluka=taluka_val,
                    example_sentence=example,
                    pronunciation=feature_str,
                    source="Linguistic Survey of Marathi Dialects",
                    status="published"
                )
                db.add(entry)
                imported += 1
        else:
            # Standard Dictionary layout
            word_idx = col_map.get("word") or col_map.get("term") or col_map.get("शब्द")
            meaning_idx = col_map.get("meaning") or col_map.get("अर्थ")

            if word_idx is None or meaning_idx is None or row[word_idx] is None or row[meaning_idx] is None:
                invalid += 1
                continue

            word = str(row[word_idx]).strip()
            meaning = str(row[meaning_idx]).strip()

            variety = str(row[col_map["variety"]]).strip() if "variety" in col_map and row[col_map["variety"]] else "Standard Marathi"
            category = str(row[col_map["category"]]).strip() if "category" in col_map and row[col_map["category"]] else "General"
            region = str(row[col_map["region"]]).strip() if "region" in col_map and row[col_map["region"]] else None
            district = str(row[col_map["district"]]).strip() if "district" in col_map and row[col_map["district"]] else None
            example = str(row[col_map["example"]]).strip() if "example" in col_map and row[col_map["example"]] else None

            existing = db.query(Entry).filter(Entry.word == word, Entry.meaning == meaning).first()
            if existing:
                duplicates += 1
                continue

            entry = Entry(
                word=word,
                meaning=meaning,
                variety=variety,
                category=category,
                region=region,
                district=district,
                example_sentence=example,
                source="Excel Import",
                status="published"
            )
            db.add(entry)
            imported += 1

    db.commit()

    print("\n" + "=" * 50)
    print("  EXCEL IMPORT COMPLETED REPORT")
    print("=" * 50)
    print(f"  Rows Read:             {rows_read}")
    print(f"  Successfully Imported: {imported}")
    print(f"  Duplicates Skipped:    {duplicates}")
    print(f"  Invalid Rows Skipped:  {invalid}")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Marathi BhashaLok data from Excel (.xlsx/.xls) into SQLite database.")
    parser.add_argument("file_path", type=str, help="Path to Excel file")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        import_excel_file(args.file_path, db)
    finally:
        db.close()

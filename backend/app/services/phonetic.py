import re

# Devanagari to IPA mapping dictionary
DEVANAGARI_IPA_MAP = {
    'अ': 'ə', 'आ': 'aː', 'इ': 'i', 'ई': 'iː', 'उ': 'u', 'ऊ': 'uː', 'ए': 'eː', 'ऐ': 'əi', 'ओ': 'oː', 'औ': 'əu',
    'क': 'kə', 'ख': 'kʰə', 'ग': 'ɡə', 'घ': 'ɡʱə', 'ङ': 'ŋə',
    'च': 't͡ʃə', 'छ': 't͡ʃʰə', 'ज': 'd͡ʒə', 'झ': 'd͡ʒʱə', 'ञ': 'ɲə',
    'ट': 'ʈə', 'ठ': 'ʈʰə', 'ड': 'ɖə', 'ढ': 'ɖʱə', 'ण': 'ɳə',
    'त': 't̪ə', 'थ': 't̪ʰə', 'द': 'd̪ə', 'ध': 'd̪ʱə', 'न': 'nə',
    'प': 'pə', 'फ': 'pʰə', 'ब': 'bə', 'भ': 'bʱə', 'म': 'mə',
    'य': 'jə', 'र': 'rə', 'ल': 'lə', 'व': 'ʋə', 'श': 'ʃə', 'ष': 'ʂə', 'स': 'sə', 'ह': 'ɦə', 'ळ': 'ɭə',
    'ा': 'aː', 'ि': 'i', 'ी': 'iː', 'ु': 'u', 'ू': 'uː', 'े': 'eː', 'ै': 'əi', 'ो': 'oː', 'ौ': 'əu',
    'ं': 'ŋ', 'ः': 'h', 'ॅ': 'æ', 'ॉ': 'ɒ', '्': ''
}

# Devanagari to Latin Transliteration Table for Phonetic Equivalence
DEVANAGARI_TO_LATIN = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ज़': 'z', 'झ़': 'zh',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'ड़': 'd', 'ढ़': 'dh',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'फ़': 'f',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h', 'ळ': 'l', 'ऱ': 'r',
    'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'i', 'उ': 'u', 'ऊ': 'u', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'u', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ः': 'h',
    'ॅ': 'e', 'ॉ': 'o', '्': ''
}

def normalize_marathi_text(text: str) -> str:
    """Normalizes Devanagari text, removing zero-width characters and normalizing punctuation."""
    if not text:
        return ""
    text = text.replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')
    text = text.replace('़', '') # normalize nuktas
    return text.strip()

def devanagari_to_transliteration(text: str) -> str:
    """Converts Devanagari text to a readable Latin phonetic representation."""
    if not text:
        return ""
    clean = normalize_marathi_text(text)
    result = []
    for char in clean:
        result.append(DEVANAGARI_TO_LATIN.get(char, char))
    return "".join(result)

def devanagari_to_ipa(text: str) -> str:
    """Converts Devanagari dialect text into approximate International Phonetic Alphabet (IPA) representation."""
    if not text:
        return ""
    clean = normalize_marathi_text(text)
    ipa_result = []
    for char in clean:
        if char in DEVANAGARI_IPA_MAP:
            ipa_result.append(DEVANAGARI_IPA_MAP[char])
        elif char.isspace() or char in [',', '.', '?', '!']:
            ipa_result.append(char)
        else:
            ipa_result.append(char)
    return "/" + "".join(ipa_result) + "/"

def generate_indic_soundex(text: str) -> str:
    """
    Generates an Indic Soundex code for phonetic indexing of regional terms.
    Works seamlessly with both Devanagari script and Latin transliteration.
    """
    if not text:
        return ""
    
    clean_text = normalize_marathi_text(text)
    
    # If text contains Devanagari, convert to phonetic Latin representation first
    if any('\u0900' <= char <= '\u097f' for char in clean_text):
        clean_text = devanagari_to_transliteration(clean_text)

    clean_text = re.sub(r'[^a-zA-Z]', '', clean_text).lower()
    if not clean_text:
        return ""

    # Soundex mapping buckets for Indic phonetic groups:
    # 1: Velars (k, g, c, q)
    # 2: Dentals, Retroflex & Nasals (t, d, n, m)
    # 3: Labials (p, b, f, v)
    # 4: Liquids (r, l)
    # 5: Sibilants & Fricatives (s, z, h, j)
    # 6: Semi-vowels (y, w)
    soundex_map = {
        'k': '1', 'g': '1', 'q': '1', 'c': '1',
        't': '2', 'd': '2', 'n': '2', 'm': '2',
        'p': '3', 'b': '3', 'f': '3', 'v': '3',
        'r': '4', 'l': '4',
        's': '5', 'z': '5', 'h': '5', 'j': '5',
        'y': '6', 'w': '6'
    }

    first_char = clean_text[0].upper()
    code = [first_char]

    for char in clean_text[1:]:
        digit = soundex_map.get(char, '0')
        if digit != '0' and (not code or code[-1] != digit):
            code.append(digit)
        if len(code) == 4:
            break

    while len(code) < 4:
        code.append('0')

    return "".join(code)

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein Distance for fuzzy string matching."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def phonetic_similarity(s1: str, s2: str) -> float:
    """Computes normalized phonetic similarity between two terms (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    s1_norm = devanagari_to_transliteration(s1).lower()
    s2_norm = devanagari_to_transliteration(s2).lower()
    dist = levenshtein_distance(s1_norm, s2_norm)
    max_len = max(len(s1_norm), len(s2_norm))
    if max_len == 0:
        return 1.0
    return max(0.0, 1.0 - (dist / max_len))

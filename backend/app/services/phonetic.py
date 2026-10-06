import re

# Devanagari to IPA mapping approximation dictionary
DEVANAGARI_IPA_MAP = {
    'अ': 'ə', 'आ': 'aː', 'इ': 'i', 'ई': 'iː', 'उ': 'u', 'ऊ': 'uː', 'ए': 'eː', 'ऐ': 'əi', 'ओ': 'oː', 'औ': 'əu',
    'क': 'kə', 'ख': 'kʰə', 'ग': 'ɡə', 'घ': 'ɡʱə', 'ङ': 'ŋə',
    'च': 't͡ʃə', 'छ': 't͡ʃʰə', 'ज': 'd͡ʒə', 'झ': 'd͡ʒʱə', 'ञ': 'ɲə',
    'ट': 'ʈə', 'ठ': 'ʈʰə', 'ड': 'ɖə', 'ढ': 'ɖʱə', 'ण': 'ɳə',
    'त': 't̪ə', 'थ': 't̪ʰə', 'द': 'd̪ə', 'ध': 'd̪ʱə', 'न': 'nə',
    'प': 'pə', 'फ': 'pʰə', 'ब': 'bə', 'भ': 'bʱə', 'म': 'mə',
    'य': 'jə', 'र': 'rə', 'ल': 'lə', 'व': 'ʋə', 'श': 'ʃə', 'ष': 'ʂə', 'स': 'sə', 'ह': 'ɦə', 'ळ': 'ɭə',
    'ा': 'aː', 'ि': 'i', 'ी': 'iː', 'ु': 'u', 'ू': 'uː', 'े': 'eː', 'ै': 'əi', 'ो': 'oː', 'ौ': 'əu', 'ं': 'ŋ', 'ः': 'h'
}

def devanagari_to_ipa(text: str) -> str:
    """Converts Devanagari dialect text into approximate International Phonetic Alphabet (IPA) representation."""
    if not text:
        return ""
    ipa_result = []
    for char in text:
        if char in DEVANAGARI_IPA_MAP:
            ipa_result.append(DEVANAGARI_IPA_MAP[char])
        elif char.isspace() or char in [',', '.', '?', '!']:
            ipa_result.append(char)
        else:
            ipa_result.append(char)
    return "/" + "".join(ipa_result) + "/"

def generate_indic_soundex(text: str) -> str:
    """Generates a simplified Indic Soundex code for phonetic indexing of regional terms."""
    if not text:
        return ""
    clean_text = re.sub(r'[^\w\s]', '', text).strip().lower()
    if not clean_text:
        return ""
    
    # Soundex mapping buckets for Indic phonetic groups
    soundex_map = {
        'k': '1', 'g': '1', 'q': '1', 'c': '1',
        't': '2', 'd': '2', 'n': '2',
        'p': '3', 'b': '3', 'f': '3', 'v': '3', 'm': '3',
        'r': '4', 'l': '4',
        's': '5', 'z': '5', 'sh': '5', 'h': '5',
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

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def is_char_en_hi_safe(c: str) -> bool:
    code = ord(c)
    if 32 <= code <= 126:
        return True
    if 0x0900 <= code <= 0x097F or 0x1CD0 <= code <= 0x1CFF or 0xA8E0 <= code <= 0xA8FF:
        return True
    return False

def sanitize_en_hi_text(text: str) -> str:
    if not text:
        return ""
    filtered_chars = [c for c in text if is_char_en_hi_safe(c)]
    cleaned = "".join(filtered_chars)
    return " ".join(cleaned.split())

def is_valid_en_hi_word(word: str) -> bool:
    if not word or len(word.strip()) == 0:
        return False
    has_valid = any(('a' <= c.lower() <= 'z') or (0x0900 <= ord(c) <= 0x097F) for c in word)
    no_forbidden = all(is_char_en_hi_safe(c) for c in word)
    return has_valid and no_forbidden

test_cases = [
    "Shri李ans Parachra also pay for this program, One Dhaneva.",
    "नमस्ते भारत! आप सब कैसे हैं?",
    "وبعد study RNVS Russian привет",
    "Om Namah Shivaya 100% sacred sound"
]

for t in test_cases:
    clean = sanitize_en_hi_text(t)
    valid_words = [w for w in clean.split() if is_valid_en_hi_word(w)]
    print("INPUT :", t)
    print("CLEAN :", clean)
    print("WORDS :", valid_words)
    print("-" * 50)

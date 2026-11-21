"""Task A4: Text preprocessing shared by every Track A model and the app.

normalize(text) is applied identically at training time and at prediction time:
  1. Unicode NFKC + lower-case
  2. Remove the [SEC] placeholder that A2 put in ILSI text. Synthetic and user text never contain it,
     so keeping it would let the model learn "court-style text" as a shortcut for certain labels.
  3. Replace URLs, phone numbers and long digit runs with placeholder tokens
  4. Normalise common Roman Urdu spelling variants (nhi/nahin/nai -> nahi, kr -> kar, ...)
  5. Keep letters, digits and basic punctuation; collapse whitespace
"""

import re
import unicodedata

# Variant -> canonical. Only unambiguous variants; English words that look like Urdu ones
# (e.g. "he", "me", "main") are deliberately NOT mapped.
ROMAN_URDU_MAP = {
    "nhi": "nahi", "nahin": "nahi", "nai": "nahi", "nahee": "nahi", "nae": "nahi",
    "kr": "kar", "krna": "karna", "krne": "karne", "krdia": "kar diya", "krdiya": "kar diya",
    "kia": "kiya", "kiaa": "kiya", "kyaa": "kya",
    "hy": "hai", "hen": "hain", "hn": "hain",
    "woh": "wo", "vo": "wo", "voh": "wo",
    "mujhay": "mujhe", "mujy": "mujhe", "mjhe": "mujhe",
    "paisay": "paise", "pese": "paise", "paisy": "paise",
    "aghwa": "agwa", "aghwaa": "agwa", "agwaa": "agwa",
    "chouri": "chori", "chory": "chori",
    "chheen": "cheen", "chheena": "cheena", "chhina": "cheena", "cheena": "cheena",
    "dhamki": "dhamki", "dhamkee": "dhamki", "dhamkiyan": "dhamkiyan",
    "zevar": "zewar", "zaiwar": "zewar",
    "qatal": "qatl", "katal": "qatl",
    "goli": "goli", "golee": "goli",
    "bhai": "bhai", "bhae": "bhai",
    "ghar": "ghar", "gher": "ghar",
    "larka": "larka", "ladka": "larka", "larkay": "larke", "ladke": "larke", "larkon": "larkon",
    "pistal": "pistol", "pistool": "pistol",
    "mobil": "mobile", "mobail": "mobile",
    # chat / SMS spellings (A3b). Words that are also English (men, may, use, fir = FIR) are deliberately NOT mapped.
    "kl": "kal", "mn": "mein", 
    "tw": "to", "toh": "to", "pr": "par", "pe": "par", "py": "par",
    "k": "ke", "ky": "ke", "kay": "ke",
    "thy": "thay", "gyi": "gayi", "gai": "gayi", "gya": "gaya", "gye": "gaye",
    "huwa": "hua", "hoa": "hua", "howa": "hua",
    "mara": "maara", "mari": "maari", "mare": "maare", "marey": "maare", "maray": "maare",
    "choot": "chot", "chott": "chot",
    "bht": "bohat", "bohot": "bohat", "bahut": "bohat", "buhat": "bohat",
    "phr": "phir", "sb": "sab", "sabh": "sab",
    "eik": "ek", "aik": "ek", "yr": "yaar", "yar": "yaar",
    "ghr": "ghar", "mujhy": "mujhe", "mjy": "mujhe", "usy": "usay", 
    "krta": "karta", "krti": "karti", "krte": "karte", "kro": "karo", "krna": "karna",
    "dhamkee": "dhamki", "dhamky": "dhamki",
    "chheen": "cheen", "chheena": "cheena", "chhuri": "churi",
    "hmari": "hamari", "hmara": "hamara", "hmare": "hamare", "hmen": "hamein", "hme": "hamein",
}

_URL = re.compile(r"https?://\S+|www\.\S+")
_PHONE = re.compile(r"(\+92|0)?3\d{2}[-\s]?\d{7}")
_LONGNUM = re.compile(r"\b\d{5,}\b")
_SEC = re.compile(r"\[sec\]", re.I)
_KEEP = re.compile(r"[^a-z0-9\s'.,!?/-]")
_TOKEN = re.compile(r"[a-z]+")


def _map_token(m):
    w = m.group(0)
    return ROMAN_URDU_MAP.get(w, w)


def normalize(text):
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", str(text)).lower()
    t = _SEC.sub(" ", t)
    t = _URL.sub(" urltoken ", t)
    t = _PHONE.sub(" phonetoken ", t)
    t = _LONGNUM.sub(" numtoken ", t)
    t = _KEEP.sub(" ", t)
    t = _TOKEN.sub(_map_token, t)
    return re.sub(r"\s+", " ", t).strip()

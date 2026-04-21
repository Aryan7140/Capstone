import joblib
import os
import re

# Load model and vectorizer
_dir = os.path.dirname(os.path.abspath(__file__))
_model = joblib.load(os.path.join(_dir, "spam_model.pkl"))
_vectorizer = joblib.load(os.path.join(_dir, "spam_vectorizer.pkl"))


def classify_message(message):
    """
    Classify a single message as spam or ham.

    Returns:
        dict with keys: label, confidence, spam_probability
    """
    X = _vectorizer.transform([message])
    prediction = _model.predict(X)[0]
    probabilities = _model.predict_proba(X)[0]

    spam_prob = probabilities[1]
    ham_prob = probabilities[0]

    return {
        "label": "SPAM" if prediction == 1 else "HAM",
        "confidence": round(max(spam_prob, ham_prob) * 100, 2),
        "spam_probability": round(spam_prob * 100, 2),
        "risk_level": _get_risk_level(spam_prob)
    }


def classify_batch(messages):
    """
    Classify a list of messages.

    Returns:
        list of dicts with classification results
    """
    results = []
    for msg in messages:
        result = classify_message(msg)
        result["message"] = msg
        results.append(result)
    return results


def _get_risk_level(spam_prob):
    """Map spam probability to a risk level for digital arrest detection."""
    if spam_prob >= 0.85:
        return "CRITICAL"
    elif spam_prob >= 0.6:
        return "HIGH"
    elif spam_prob >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


# ========================================
# KEYWORD LISTS FOR SCAM DETECTION
# ========================================

# Digital arrest / impersonation scam keywords
DIGITAL_ARREST_KEYWORDS = [
    "digital arrest", "cyber arrest", "cbi", "legal action",
    "warrant", "money laundering", "arrested", "arrest", "court order", "aadhaar",
    "freeze account", "narcotics", "penalty", "illegal",
    "transfer immediately", "secure account", "compromised",
    "under surveillance", "crime branch", "enforcement",
    "customs", "illegal parcel", "drug parcel", "parcel",
    "interpol", "income tax", "ed notice", "enforcement directorate",
    "rbi", "reserve bank", "sebi", "trai",
    "pay fine", "pay penalty", "fine of", "drugs",
    "transfer funds", "transfer all", "safe account",
    "under arrest", "get arrested", "face arrest",
    "fir", "case registered", "case filed",
    "cyber crime", "cyber cell", "fraud case",
    "impersonat", "scam", "blackmail",
]

# Phishing / social engineering — ANY personal or sensitive info
PHISHING_KEYWORDS = [
    # Passwords & credentials
    "password", "passwd", "passcode", "passkey",
    "otp", "one time password", "verification code", "security code",
    "pin", "pin number", "mpin", "upi pin", "atm pin",
    "cvv", "cvv2", "cvc", "security number",
    "login", "login id", "user id", "username",
    "credentials", "secret question", "security answer",
    "two factor", "2fa", "authentication code",

    # Financial info
    "account number", "account no", "a/c number", "bank account",
    "bank details", "banking details", "account details",
    "credit card", "debit card", "card number", "card details",
    "card expiry", "expiry date", "expiration date",
    "ifsc", "ifsc code", "swift code", "routing number",
    "upi id", "upi address", "gpay", "phonepe", "paytm",
    "net banking", "internet banking",
    "wallet", "crypto wallet", "bitcoin address",

    # Identity documents
    "pan card", "pan number", "pan no",
    "aadhar number", "aadhaar number", "aadhar card", "aadhaar card",
    "aadhar no", "aadhaar no",
    "voter id", "voter card", "election card",
    "driving license", "driving licence", "dl number",
    "passport number", "passport details", "passport no",
    "ration card", "ration number",
    "ssn", "social security",

    # Personal information
    "date of birth", "dob", "birth date",
    "mother maiden name", "maiden name",
    "full name", "legal name",
    "home address", "residential address", "current address",
    "phone number", "mobile number", "contact number",
    "email id", "email address", "email password",
    "personal details", "personal information", "private information",
    "family details", "family members",
    "father name", "mother name", "spouse name",
    "salary", "income details", "income proof",
    "tax returns", "itr", "form 16",
    "employee id", "company details",

    # Biometric
    "fingerprint", "face id", "face scan", "biometric",
    "retina", "iris scan",

    # Photos / docs
    "selfie", "photo id", "identity proof", "id proof",
    "bank statement", "account statement",
    "send photo", "send document", "send copy",
    "scan of", "photo of your",

    # Generic ask patterns
    "verify your", "confirm your", "update your details",
    "click this link", "click here", "click below",
    "expiring", "expired", "reactivate",
    "validate your", "authenticate your",
]

# Urgency / threat keywords
THREAT_KEYWORDS = [
    "immediately", "urgent", "right now", "within 24 hours",
    "within 1 hour", "last warning", "final notice",
    "act now", "do it now", "as soon as possible", "asap",
    "account will be", "will be blocked", "will be frozen",
    "will be closed", "will be suspended", "will be terminated",
    "will be deactivated", "will be locked",
    "legal consequences", "police",
    "investigation", "suspicious activity", "unauthorized",
    "verify identity", "or else", "otherwise",
    "non compliance", "failure to comply",
    "don't tell anyone", "keep this confidential",
    "do not share", "do not inform", "stay on the line",
    "you have been selected", "you have been chosen",
    "risk of", "danger", "threatening",
    "pay now", "send now", "transfer now",
    "you must", "you need to", "you are required",
    "deadline", "time is running", "hurry",
    "or we will", "consequences", "action will be taken",
]


# ========================================
# VIOLENCE & PHYSICAL THREAT PHRASES
# (Multi-word — high confidence, high weight)
# ========================================
VIOLENCE_THREAT_PHRASES = [
    # Direct death threats
    "kill you", "murder you", "end you", "finish you off",
    "destroy you", "eliminate you", "get rid of you",
    "make you disappear", "bury you", "put you in the ground",
    "six feet under", "put you down",
    "i'll kill", "i will kill", "i'm going to kill", "im going to kill",
    "going to kill", "gonna kill", "want to kill", "gotta kill",
    "i'll murder", "i will murder", "going to murder", "gonna murder",
    "i'll end you", "i will end you",
    "kill him", "kill her", "kill them", "kill his", "kill her",
    "murder him", "murder her", "murder them",

    # Physical violence
    "beat you", "beat you up", "beat the hell out",
    "beat the shit out", "beat the crap out",
    "hurt you", "harm you", "injure you",
    "attack you", "assault you",
    "hit you", "punch you", "slap you", "kick you",
    "stab you", "shoot you", "cut you", "burn you",
    "strangle you", "choke you",
    "break your", "smash your", "crush your",
    "snap your neck", "break your legs", "break your face",
    "break your bones", "crack your skull",
    "bash your", "pound you", "pummel you",
    "rip you apart", "tear you apart",
    "beat him", "beat her", "beat them",
    "hurt him", "hurt her", "hurt them",
    "stab him", "stab her", "shoot him", "shoot her",

    # Death references targeting someone
    "you're dead", "you are dead", "you will die",
    "you'll die", "you're gonna die", "you are going to die",
    "your days are numbered", "count your days",
    "your last day", "your last breath",
    "won't live to see", "won't survive",
    "not going to survive", "not gonna survive",
    "he's dead", "she's dead", "they're dead",
    "he will die", "she will die",

    # Weapon references
    "pull the trigger", "put a bullet in",
    "shoot you dead", "blow your brains",
    "blow you up", "blow your head",
    "slit your throat", "slash your",
    "use my gun on", "bring a knife",
    "i have a gun", "i have a knife",
    "i'll shoot", "i will shoot",

    # Coming after someone
    "i'll find you", "i will find you", "gonna find you",
    "come for you", "coming for you", "coming after you",
    "hunt you", "hunt you down", "hunting you",
    "track you down", "find where you live",
    "come to your house", "show up at your",
    "i know where you are", "i'll come there",

    # Making someone suffer
    "make you suffer", "make you pay", "make you bleed",
    "you'll suffer", "you will suffer",
    "you'll regret", "you will regret", "gonna regret",
    "teach you a lesson", "show you what happens",
    "pay for this", "pay for what you did",

    # Intimidation phrases (direct)
    "watch your back", "sleep with one eye open",
    "better watch out", "better run", "better hide",
    "nowhere to hide", "can't hide from me",
    "can't run from me", "no escape", "nowhere to run",
    "be afraid", "be very afraid", "be scared",
    "should be scared", "you should fear",
    "fear for your life", "fear me",
    "don't test me", "try me",

    # Conditional threats
    "or i'll hurt", "or i will hurt",
    "or i'll kill", "or i will kill",
    "or you'll regret", "or you will regret",

    # Hindi / Hinglish violence phrases (romanized)
    "maar dunga", "maar dalunga", "jaan se maar",
    "kaat dunga", "kaat dalunga",
    "goli maar dunga", "goli maar", "goli chalaunga",
    "jaan le lunga", "jaan lena", "jaan se khatam",
    "tujhe khatam", "khatam kar dunga", "khatam karunga",
    "maarunga", "peetunga", "dho dunga",
    "chaku maar", "chaaku maar", "chaaku se",
    "zinda nahi chodunga", "zinda nahi rahunga",
    "tujhe udaa dunga", "udaa dunga",
    "dhundh ke maarunga", "dhundh lunga",
    "tere tukde kar dunga", "tukde tukde",
    "haddi tod dunga", "haath tod dunga",
    "khoon kar dunga", "khoon nikal dunga",
    "tapka dunga", "supari de dunga",
    "tera kaam tamam", "kaam tamam",
    "you'll pay for", "if you don't pay",
    "if you don't give", "do it or",
    "comply or", "obey or",
]

# Violence-related keywords (single words, medium weight)
# Matched with word-boundary to avoid "skill" matching "kill" etc.
VIOLENCE_KEYWORDS = [
    "kill", "murder", "stab", "shoot", "attack", "assault",
    "strangle", "choke", "kidnap", "abduct",
    "torture", "torment", "maim", "mutilate",
    "slaughter", "massacre", "execute", "behead",
    "assassin", "assassinate", "hitman",
    "weapon", "gun", "pistol", "rifle", "firearm",
    "knife", "blade", "dagger", "machete",
    "bomb", "explosive", "grenade", "dynamite",
    "poison", "acid", "arson",
    "bloodbath", "bloodshed",
    "hostage", "ransom",
    "terrorize", "terrorise", "terror",
    "lynch", "ambush",
    "revenge", "avenge", "retaliate", "vengeance",
    "homicide", "manslaughter",
    "sniper", "ammunition", "bullet",
    "die", "dead", "death",
    "corpse", "grave", "bury",
    "throat", "skull",
]


# ========================================
# EXTORTION & BLACKMAIL PHRASES
# ========================================
EXTORTION_PHRASES = [
    # Direct money demands
    "give me money", "give me cash", "give money",
    "give me the money", "hand over money", "hand over cash",
    "hand over the money", "bring money", "bring cash",
    "bring the money", "come with money", "come with cash",
    "send me money", "send money now", "send me cash",
    "wire money", "wire me money", "wire transfer now",
    "pay me", "pay up", "pay me now",
    "transfer money to", "transfer funds to",
    "deposit money", "deposit cash",
    "meet me and give", "meet and pay",
    "bring payment", "make a payment now",
    "give me what i want",

    # Conditional money demands
    "pay or else", "pay or i", "pay or you",
    "money or else", "money or i will", "money or i'll",
    "cash or else", "cash or i will",
    "give money or", "send money or",
    "pay if you want", "pay to keep",
    "pay me or", "transfer or",

    # Blackmail
    "i have your photos", "i have your videos",
    "i have your pictures", "i have screenshots",
    "i have evidence", "i have proof",
    "i'll expose", "i will expose", "gonna expose",
    "i'll leak", "i will leak", "gonna leak",
    "i'll release", "i will release",
    "i'll share your", "i will share your",
    "i'll post your", "i will post your",
    "i'll send your", "i will send your",
    "i'll tell everyone", "i will tell everyone",
    "i'll show everyone", "i will show everyone",
    "i'll upload", "i will upload",
    "delete for money", "pay to delete",
    "pay me to keep", "pay to keep quiet",
    "keep quiet or", "keep this secret or",
    "don't want everyone to see", "don't want this shared",
    "i'll ruin you", "i will ruin you",
    "ruin your life", "destroy your life",
    "destroy your career", "ruin your reputation",
    "ruin your marriage", "destroy your family",
    "end your career", "make your life miserable",
    "make your life hell",

    # Protection racket / implied threats
    "pay for protection", "protection money",
    "something bad will happen", "something might happen",
    "accidents happen", "would be a shame if",
    "nice place you have", "nice family you have",
    "nice business you have", "hate to see something happen",

    # Hindi / Hinglish extortion phrases (romanized)
    "paise de", "paisa de", "paisa bhej",
    "paise nikal", "rupay de", "rupaye de",
    "paise de nahi to", "paisa de warna",
    "paise la", "paise leke aa", "paise lekar aa",
    "hafta de", "hafta dena padega",
    "warna dekh", "nahi diya to",
    "paisa nahi diya", "dega ya nahi",
]

EXTORTION_KEYWORDS = [
    "blackmail", "extort", "extortion", "ransom",
    "bribe", "bribery", "payoff", "shakedown",
    "coerce", "coercion", "exploit",
    "hush money", "protection money",
]


# ========================================
# HARASSMENT & STALKING PHRASES
# ========================================
HARASSMENT_PHRASES = [
    # Location knowledge
    "i know where you live", "know your address",
    "know where you stay", "know your home",
    "been to your house", "seen your house",
    "i know your location", "found your address",

    # Family knowledge / threats
    "i know your family", "know your wife",
    "know your husband", "know your children",
    "know your kids", "know your parents",
    "know your mother", "know your father",
    "know your sister", "know your brother",
    "know your girlfriend", "know your boyfriend",
    "your family will", "your kids will",
    "your wife will", "your husband will",

    # Surveillance
    "watching you", "been watching you",
    "following you", "been following you",
    "tracking you", "keeping tabs on you",
    "i saw you at", "i see you",
    "i've seen you", "i have seen you",
    "surveillance on you", "keeping an eye on you",
    "i followed you", "i'm outside your",

    # Persistence
    "won't leave you alone", "never leave you alone",
    "won't stop until", "not going to stop",
    "can't get away from me", "can't escape me",
    "you can't escape", "no way out",
    "i'll never stop", "i will never stop",
    "always watching", "always following",

    # Hindi / Hinglish harassment phrases (romanized)
    "pata hai tu kahan rehta", "pata hai tere ghar",
    "tujhe follow kar raha", "nazar rakh raha",
    "tere ghar aaunga", "tere ghar tak",
    "tere peeche", "peecha karunga",
    "tere ghar ke bahar", "tera pata hai mujhe",
]

HARASSMENT_KEYWORDS = [
    "stalk", "stalking", "stalker",
    "harass", "harassment", "harassing",
    "molest", "molestation",
    "bully", "bullying",
    "predator", "creep",
    "obsessed", "obsession",
    "spy", "spying",
    "pervert", "perverted",
]


# ========================================
# INTIMIDATION PHRASES & KEYWORDS
# ========================================
INTIMIDATION_PHRASES = [
    # Regret / sorry warnings
    "you'll be sorry", "you'll regret this",
    "you will be sorry", "you will regret this",
    "you're going to regret", "gonna be sorry",

    # Future threats
    "wait and see", "just wait", "you just wait",
    "you'll see what happens", "you will see",
    "mark my words", "remember my words",
    "remember this day", "remember what i said",

    # Not over
    "this isn't over", "this is not over",
    "it's not over", "far from over",
    "i'll be back", "i will be back",
    "i'm coming back", "coming back for you",
    "you haven't seen the last", "last of me",

    # Don't mess with me
    "don't test me", "don't push me",
    "don't mess with me", "don't mess with",
    "don't make me angry", "you won't like me when",
    "you don't want to see", "cross me",
    "wrong person to mess with", "wrong person",
    "you have no idea what i", "you don't know who",
    "do you know who i am", "know who you're dealing with",

    # Connected / powerful
    "i have connections", "i have people",
    "i know people", "people who can",
    "my boys will", "my people will", "my guys will",
    "i have friends in", "i know powerful",
    "i can make one call", "one phone call",

    # General menace
    "you're finished", "you are finished",
    "it's over for you", "this is your end",
    "you're done", "you are done",
    "i'll make sure", "i will make sure",
    "you won't get away", "won't get away with",
    "there will be hell", "hell to pay",
    "you asked for it", "you deserve this",
    "brought this on yourself",

    # Hindi / Hinglish intimidation phrases (romanized)
    "dekh lunga", "tujhe dekh lunga",
    "bahut pachtayega", "pachtayega tu",
    "aakhri warning", "aakhri mauka",
    "nahi chodunga", "tujhe chodunga nahi",
    "meri baari aayegi", "dekhna tujhe",
    "beta tujhe", "tera career khatam",
    "bahut bura hoga", "acha nahi hoga",
    "anjaam bura hoga", "bhugat lena",
    "aukaat dikhaunga", "aukaat bata dunga",
]

INTIMIDATION_KEYWORDS = [
    "threatening", "menacing", "ominous",
    "warning", "warned", "beware",
    "consequences", "payback", "retribution",
    "punish", "punishment",
    "wrath", "fury",
    "regret", "suffer",
    "dare",
]


# Aggregate all keywords (for reference/export)
ALL_SCAM_KEYWORDS = (
    DIGITAL_ARREST_KEYWORDS + PHISHING_KEYWORDS + THREAT_KEYWORDS +
    VIOLENCE_KEYWORDS + EXTORTION_KEYWORDS +
    HARASSMENT_KEYWORDS + INTIMIDATION_KEYWORDS
)

# ========================================
# SENSITIVE INFO — if someone asks for ANY of these, it's a scam
# ========================================
SENSITIVE_INFO_KEYWORDS = [
    # Any type of password
    "password", "passwd", "passcode", "passkey", "pin",
    "mpin", "upi pin", "atm pin", "pin number",
    # OTP / verification
    "otp", "one time password", "verification code",
    "security code", "authentication code", "2fa",
    # Card details
    "cvv", "cvv2", "cvc", "card number", "card details",
    "credit card", "debit card", "card expiry",
    # Account / banking
    "account number", "account no", "bank details",
    "bank account", "account details", "a/c number",
    "net banking", "internet banking", "ifsc",
    "upi id", "upi pin",
    # Identity / personal docs
    "aadhaar number", "aadhar number", "aadhaar no", "aadhar no",
    "pan number", "pan no", "pan card",
    "passport number", "passport no", "dl number",
    "driving license", "voter id", "ssn", "social security",
    # Personal info
    "date of birth", "dob", "mother maiden name",
    "home address", "residential address",
    "salary", "income details",
    "personal details", "personal information",
    "private information", "family details",
    # Login credentials
    "login", "login id", "user id", "username",
    "credentials", "secret question", "security answer",
    "email password",
    # Biometric
    "fingerprint", "face id", "biometric",
    # Photos of docs
    "selfie", "photo id", "id proof", "identity proof",
    "bank statement",
]

REQUEST_PHRASES = [
    "tell me", "send me", "share your", "give me",
    "provide your", "enter your", "type your",
    "tell me your", "send me your", "share your",
    "give me your", "provide me your", "provide me with",
    "i need your", "we need your", "submit your",
    "input your", "fill in your", "disclose your",
    "hand over your", "reveal your", "what is your",
    "what's your", "whats your",
    "send your", "give your", "share the",
    "tell the", "provide the", "need your",
    "require your", "asking for your",
]


# ========================================
# HELPER: WORD-BOUNDARY KEYWORD MATCHING
# ========================================
def _match_with_boundary(text, keywords):
    """
    Match keywords using word-start boundary to prevent partial matches.
    Example: 'kill' matches 'kill', 'killed', 'killing' but NOT 'skill'.
    Multi-word phrases use simple substring matching.
    """
    matched = []
    for kw in keywords:
        if ' ' in kw:
            # Multi-word phrase: substring match is fine
            if kw in text:
                matched.append(kw)
        else:
            # Single word: use word-start boundary
            if re.search(r'\b' + re.escape(kw), text):
                matched.append(kw)
    return matched


# ========================================
# MAIN DETECTION ENGINE
# ========================================
def detect_digital_arrest(message):
    """
    Comprehensive threat detection combining ML spam classification
    with multi-category keyword/phrase-based detection.

    Detection categories:
    - Digital arrest / impersonation scams
    - Phishing / social engineering
    - Violence / physical threats
    - Extortion / blackmail
    - Harassment / stalking
    - Intimidation / menacing behavior
    - Urgency / pressure tactics

    Scoring: max(ML_score, rule_score) with cross-category synergy bonuses.
    This ensures that EITHER a high ML score OR strong keyword signals
    will produce a high threat score — both paths can independently
    flag a message as dangerous.
    """
    # ── ML CLASSIFICATION ─────────────────────────────────
    ml_result = classify_message(message)
    spam_prob = ml_result["spam_probability"]  # already 0-100

    msg_lower = message.lower()

    # ── MATCH ALL CATEGORIES ──────────────────────────────

    # Original categories (backward-compatible substring match)
    matched_arrest = [kw for kw in DIGITAL_ARREST_KEYWORDS if kw in msg_lower]
    matched_phishing = [kw for kw in PHISHING_KEYWORDS if kw in msg_lower]
    matched_threat_urgency = [kw for kw in THREAT_KEYWORDS if kw in msg_lower]

    # New categories (phrases = substring, keywords = word-boundary)
    matched_violence_phrases = [p for p in VIOLENCE_THREAT_PHRASES if p in msg_lower]
    matched_violence_kw = _match_with_boundary(msg_lower, VIOLENCE_KEYWORDS)
    matched_extortion_phrases = [p for p in EXTORTION_PHRASES if p in msg_lower]
    matched_extortion_kw = _match_with_boundary(msg_lower, EXTORTION_KEYWORDS)
    matched_harassment_phrases = [p for p in HARASSMENT_PHRASES if p in msg_lower]
    matched_harassment_kw = _match_with_boundary(msg_lower, HARASSMENT_KEYWORDS)
    matched_intimidation_phrases = [p for p in INTIMIDATION_PHRASES if p in msg_lower]
    matched_intimidation_kw = _match_with_boundary(msg_lower, INTIMIDATION_KEYWORDS)

    # ── RULE-BASED THREAT SCORE ───────────────────────────
    # Each category independently contributes a score.
    # We take the MAX across categories, then add synergy bonuses.
    rule_score = 0
    threat_categories = []

    # Violence phrases → immediate high threat (75–95)
    if matched_violence_phrases:
        s = 75 + min(len(matched_violence_phrases) * 8, 20)
        rule_score = max(rule_score, s)
        threat_categories.append("VIOLENCE")

    # Violence keywords alone (35–80)
    if matched_violence_kw:
        s = 35 + min(len(matched_violence_kw) * 12, 45)
        rule_score = max(rule_score, s)
        if "VIOLENCE" not in threat_categories:
            threat_categories.append("VIOLENCE")

    # Extortion phrases → high threat (70–90)
    if matched_extortion_phrases:
        s = 70 + min(len(matched_extortion_phrases) * 8, 20)
        rule_score = max(rule_score, s)
        threat_categories.append("EXTORTION")

    # Extortion keywords (30–70)
    if matched_extortion_kw:
        s = 30 + min(len(matched_extortion_kw) * 12, 40)
        rule_score = max(rule_score, s)
        if "EXTORTION" not in threat_categories:
            threat_categories.append("EXTORTION")

    # Harassment phrases (60–85)
    if matched_harassment_phrases:
        s = 60 + min(len(matched_harassment_phrases) * 10, 25)
        rule_score = max(rule_score, s)
        threat_categories.append("HARASSMENT")

    # Harassment keywords (35–70)
    if matched_harassment_kw:
        s = 35 + min(len(matched_harassment_kw) * 10, 35)
        rule_score = max(rule_score, s)
        if "HARASSMENT" not in threat_categories:
            threat_categories.append("HARASSMENT")

    # Intimidation phrases (55–80)
    if matched_intimidation_phrases:
        s = 55 + min(len(matched_intimidation_phrases) * 10, 25)
        rule_score = max(rule_score, s)
        threat_categories.append("INTIMIDATION")

    # Intimidation keywords (30–65)
    if matched_intimidation_kw:
        s = 30 + min(len(matched_intimidation_kw) * 10, 35)
        rule_score = max(rule_score, s)
        if "INTIMIDATION" not in threat_categories:
            threat_categories.append("INTIMIDATION")

    # Digital arrest keywords (30–80)
    if matched_arrest:
        s = 30 + min(len(matched_arrest) * 15, 50)
        rule_score = max(rule_score, s)
        threat_categories.append("DIGITAL_ARREST")

    # Phishing keywords (25–70)
    if matched_phishing:
        s = 25 + min(len(matched_phishing) * 12, 45)
        rule_score = max(rule_score, s)
        threat_categories.append("PHISHING")

    # Threat/urgency keywords (15–55)
    if matched_threat_urgency:
        s = 15 + min(len(matched_threat_urgency) * 10, 40)
        rule_score = max(rule_score, s)

    # Cross-category synergy bonus
    if len(threat_categories) >= 3:
        rule_score = min(rule_score + 20, 100)
    elif len(threat_categories) >= 2:
        rule_score = min(rule_score + 10, 100)

    # ── COMBINE ML + RULE SCORES ──────────────────────────
    # Take the HIGHER of ML or rule-based score.
    # If both contribute, add a small synergy bonus.
    combined_score = max(spam_prob, rule_score)

    if spam_prob >= 20 and rule_score >= 20:
        combined_score = min(combined_score + 10, 100)

    # ── COLLECT ALL MATCHED KEYWORDS ──────────────────────
    all_matched = (
        matched_arrest + matched_phishing + matched_threat_urgency +
        matched_violence_phrases + matched_violence_kw +
        matched_extortion_phrases + matched_extortion_kw +
        matched_harassment_phrases + matched_harassment_kw +
        matched_intimidation_phrases + matched_intimidation_kw
    )
    # Deduplicate while preserving order
    seen = set()
    matched_keywords = []
    for kw in all_matched:
        if kw not in seen:
            seen.add(kw)
            matched_keywords.append(kw)

    keyword_score = min(len(matched_keywords) * 15, 100)

    # ── SENSITIVE INFO CHECK (existing logic) ─────────────
    has_sensitive_info = any(kw in msg_lower for kw in SENSITIVE_INFO_KEYWORDS)
    has_request_phrase = any(kw in msg_lower for kw in REQUEST_PHRASES)

    # ── DECISION LOGIC ────────────────────────────────────
    # Ordered by severity (highest priority first)

    # Rule 1: Asking for ANY sensitive info = ALWAYS scam
    if has_sensitive_info and has_request_phrase:
        decision = "DIGITAL_ARREST_SCAM"
        combined_score = max(combined_score, 85)

    # Rule 2: Violence phrases = ALWAYS scam
    elif matched_violence_phrases:
        decision = "DIGITAL_ARREST_SCAM"
        combined_score = max(combined_score, 75)

    # Rule 3: Extortion phrases = ALWAYS scam
    elif matched_extortion_phrases:
        decision = "DIGITAL_ARREST_SCAM"
        combined_score = max(combined_score, 70)

    # Rule 4: High combined score
    elif combined_score >= 55:
        decision = "DIGITAL_ARREST_SCAM"

    # Rule 5: Multiple digital arrest keywords
    elif len(matched_arrest) >= 2:
        decision = "DIGITAL_ARREST_SCAM"

    # Rule 6: High ML confidence + any keyword
    elif spam_prob >= 80 and len(matched_keywords) >= 1:
        decision = "DIGITAL_ARREST_SCAM"

    # Rule 7: Many keywords across categories
    elif len(matched_keywords) >= 3:
        decision = "DIGITAL_ARREST_SCAM"

    # Rule 8: Multiple phishing signals
    elif len(matched_phishing) >= 2:
        decision = "DIGITAL_ARREST_SCAM"

    # Rule 9: Combined arrest + threat signals
    elif len(matched_arrest) + len(matched_threat_urgency) >= 3:
        decision = "DIGITAL_ARREST_SCAM"

    # Rule 10: Harassment phrases → at least SUSPICIOUS
    elif matched_harassment_phrases:
        decision = "SUSPICIOUS"
        combined_score = max(combined_score, 55)

    # Rule 11: Sensitive info mentioned (without explicit request)
    elif has_sensitive_info:
        decision = "SUSPICIOUS"
        combined_score = max(combined_score, 50)

    # Rule 12: Moderate signals
    elif (combined_score >= 25
            or spam_prob >= 40
            or len(matched_keywords) >= 2
            or len(matched_phishing) >= 1
            or matched_intimidation_phrases
            or matched_violence_kw):
        decision = "SUSPICIOUS"

    else:
        decision = "SAFE"

    # Effective threat probability: if rules detect a threat,
    # the displayed probability should reflect that — not just ML.
    effective_probability = round(max(spam_prob, rule_score, combined_score), 2)

    return {
        "decision": decision,
        "spam_probability": effective_probability,
        "ml_spam_probability": ml_result["spam_probability"],
        "confidence": ml_result["confidence"],
        "keyword_matches": matched_keywords,
        "keyword_score": keyword_score,
        "rule_score": round(rule_score, 2),
        "combined_score": round(combined_score, 2),
        "threat_categories": threat_categories,
        "message": message
    }

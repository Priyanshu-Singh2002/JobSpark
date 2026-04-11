import re

import spacy

nlp = spacy.load("en_core_web_sm")

# Expanded role keywords (substring match, case-insensitive)
JOB_TITLE_KEYWORDS = [
    "Software Engineer",
    "Data Scientist",
    "Web Developer",
    "ML Engineer",
    "DevOps Engineer",
    "Full Stack Developer",
    "Backend Developer",
    "Frontend Developer",
    "Data Analyst",
    "AI Engineer",
    "AI-Engineer",
    "Product Manager",
    "Project Manager",
    "UI/UX",
    "UI/UX Designer",
    "Business Analyst",
    "System Administrator",
    "Network Engineer",
    "Database Administrator",
    "Cybersecurity Analyst",
    "Cloud Engineer",
    "Mobile App Developer",
    "Game Developer",
    "Blockchain Developer",
    "Digital Marketing",
    "ERP Consultant",
    "Research Scientist",
    "Technical Writer",
    "Quality Assurance Engineer",
    "Sales Engineer",
    "Marketing Specialist",
    "Content Writer",
    "Graphic Designer",
    "SEO Specialist",
    "Social Media Manager",
    "Customer Support Specialist",
    "Human Resources Manager",
    "Financial Analyst",
    "Accountant",
    "Operations Manager",
]

# Common Indian cities / regions if spaCy misses GPE
LOCATION_HINTS = [
    "bengaluru",
    "bangalore",
    "mumbai",
    "delhi",
    "hyderabad",
    "pune",
    "chennai",
    "kolkata",
    "gurgaon",
    "gurugram",
    "noida",
    "ahmedabad",
    "kochi",
    "jaipur",
    "indore",
    "coimbatore",
]


def _parse_min_salary_lakhs(text: str):
    """Extract a minimum salary in lakhs per annum from natural language."""
    t = text.lower()
    # Range: "5-8 LPA", "5 to 8 lakhs" → use lower bound
    range_m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|l\.?p\.?a\.?)?",
        t,
    )
    if range_m:
        try:
            return float(range_m.group(1))
        except ValueError:
            pass

    # Single amount with LPA / lakhs
    lakhs_m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|l\.?p\.?a\.?)\b", t
    )
    if lakhs_m:
        try:
            return float(lakhs_m.group(1))
        except ValueError:
            pass

    # "12 lakh" without LPA suffix
    plain_m = re.search(r"(\d+(?:\.\d+)?)\s+lakh", t)
    if plain_m:
        try:
            return float(plain_m.group(1))
        except ValueError:
            pass

    # Crore (e.g. 1 crore → 100 lakhs) — rare in fresher apps
    cr_m = re.search(r"(\d+(?:\.\d+)?)\s*crore", t)
    if cr_m:
        try:
            return float(cr_m.group(1)) * 100.0
        except ValueError:
            pass

    return None


def _match_title(transcript_lower: str):
    """Longest keyword match wins (more specific titles first)."""
    best = ""
    for jtitle in sorted(JOB_TITLE_KEYWORDS, key=len, reverse=True):
        if jtitle.lower() in transcript_lower:
            if len(jtitle) > len(best):
                best = jtitle
    return best


def _fallback_title(doc, transcript: str, location_guess: str):
    """Use cleaned tokens when no keyword matched."""
    skip = set()
    if location_guess:
        skip.add(location_guess.lower())
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "FAC", "MONEY", "DATE", "TIME"):
            skip.add(ent.text.lower())

    words = []
    for token in doc:
        if token.is_stop or not token.is_alpha:
            continue
        lw = token.text.lower()
        if lw in skip or len(lw) < 2:
            continue
        if lw in ("job", "jobs", "opening", "openings"):
            continue
        words.append(token.text)

    while words and words[-1].lower() in ("job", "jobs", "opening", "openings"):
        words.pop()

    if len(words) >= 2:
        return " ".join(words[:6])
    if words:
        return words[0]

    # Last resort: strip obvious location/salary phrases
    cleaned = transcript
    for phrase in (
        "jobs in",
        "job in",
        "find",
        "search",
        "looking for",
        "need",
        "want",
    ):
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > 2:
        return cleaned[:80]
    return ""


def Extract_filter(transcript: str):
    """
    Map voice/text search to filter fields. Uses spaCy entities + heuristics.
    Returns keys aligned with the job filter form / DB loader (no raw salary string).
    """
    raw = (transcript or "").strip()
    t_lower = raw.lower()
    doc = nlp(raw)

    filters = {
        "title": "",
        "location": "",
        "min_salary_lakhs": None,
        "work_mode": "",
        "employment_type": "",
        "experience": "",
    }

    # --- Work mode (matches DB column work_mode) ---
    if re.search(r"\bhybrid\b", t_lower):
        filters["work_mode"] = "hybrid"
    elif re.search(r"\b(wfh|work from home|work-from-home)\b", t_lower):
        filters["work_mode"] = "wfh"
    elif re.search(r"\bremote\b", t_lower):
        filters["work_mode"] = "remote"
    elif re.search(r"\bon[-\s]?site\b|\bin[-\s]?office\b|\boffice\s+job\b", t_lower):
        filters["work_mode"] = "office"

    # --- Employment type ---
    if re.search(r"part[\s-]*time|parttime|\bpart\s+timer\b", t_lower):
        filters["employment_type"] = "part_time"
    elif re.search(r"\bfull[\s-]*time\b", t_lower):
        filters["employment_type"] = "full_time"

    # --- Location: prefer spaCy GPE/LOC; take first non-overlapping ---
    loc_parts = []
    seen = set()
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC") and ent.text.lower() not in seen:
            loc_parts.append(ent.text.strip())
            seen.add(ent.text.lower())
    if loc_parts:
        filters["location"] = ", ".join(loc_parts[:2])
    else:
        for city in LOCATION_HINTS:
            if re.search(r"\b" + re.escape(city) + r"\b", t_lower):
                filters["location"] = city.title()
                break

    # --- Salary ---
    lakhs = _parse_min_salary_lakhs(raw)
    if lakhs is not None:
        filters["min_salary_lakhs"] = lakhs

    # --- Experience ---
    if re.search(
        r"\b(fresher|fresh graduate|entry level|0\s*years?|no experience)\b",
        t_lower,
    ):
        filters["experience"] = "fresher"
    else:
        m = re.search(
            r"\b(\d+)\s*\+?\s*(years?|yrs?)\b",
            t_lower,
        )
        if m:
            y = int(m.group(1))
            if y <= 1:
                filters["experience"] = "1"
            else:
                filters["experience"] = "2"

    # --- Job title: keyword list, then fallback ---
    title_hit = _match_title(t_lower)
    if title_hit:
        filters["title"] = title_hit
    else:
        fb = _fallback_title(doc, raw, filters["location"])
        if fb:
            filters["title"] = fb

    # Work-mode-only utterances should not force a bogus title
    if filters.get("work_mode") and not title_hit:
        tonly = filters["title"].lower().strip()
        if tonly in ("remote", "work from home", "wfh", "hybrid", "office", "work mode"):
            filters["title"] = ""

    return filters

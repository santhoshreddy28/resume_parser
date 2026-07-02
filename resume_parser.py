"""
Smart Resume Parser - Core Logic
Extracts structured info (name, contact, skills, education, experience)
from PDF/DOCX resumes.
"""

import re
import json
import io

import fitz  # PyMuPDF
import docx  # python-docx

# spaCy is optional at runtime — if the model isn't downloaded yet,
# we fall back to regex/heuristic extraction so the app still works.
try:
    import spacy
    try:
        NLP = spacy.load("en_core_web_sm")
    except OSError:
        NLP = None
except ImportError:
    NLP = None


# ---------------------------------------------------------------------
# 1. TEXT EXTRACTION
# ---------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from a PDF file given as bytes."""
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract raw text from a DOCX file given as bytes."""
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to the correct extractor based on file extension."""
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX.")


# ---------------------------------------------------------------------
# 2. CLEANING
# ---------------------------------------------------------------------

def clean_text(raw_text: str) -> str:
    """Normalize whitespace and strip junk characters."""
    text = raw_text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# ---------------------------------------------------------------------
# 3. FIELD EXTRACTION HELPERS
# ---------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# Handles common formats: 9876543210 | 98765 43210 | +91 98765 43210
# | +91-9988776655 | (123) 456-7890 | 123-456-7890
PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[-.\s]?)?"                       # optional country code
    r"(?:\d{5}[-.\s]\d{5}"                         # 5+5 split, e.g. 98765 43210
    r"|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"         # 3-3-4 split, e.g. 123-456-7890
    r"|\d{10})"                                     # plain 10 digits
)
LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9_-]+")
GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_-]+")

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies", "key skills"],
    "education": ["education", "academic background", "qualifications"],
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "personal projects", "academic projects"],
    "certifications": ["certifications", "certificates", "licenses"],
}

# A reasonably broad skills vocabulary for keyword matching.
SKILLS_DB = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "r", "go", "rust",
    "html", "css", "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "streamlit", "spring boot", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "keras", "opencv", "nlp", "spacy", "nltk", "machine learning", "deep learning",
    "data analysis", "data visualization", "matplotlib", "seaborn", "power bi", "tableau",
    "excel", "aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "linux",
    "mysql", "postgresql", "mongodb", "sqlite", "rest api", "graphql", "selenium",
    "beautifulsoup", "web scraping", "agile", "scrum", "jira", "postman", "ci/cd",
    "jenkins", "unit testing", "pytest",
]


def extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else ""


def extract_linkedin(text: str) -> str:
    match = LINKEDIN_RE.search(text)
    return match.group(0) if match else ""


def extract_github(text: str) -> str:
    match = GITHUB_RE.search(text)
    return match.group(0) if match else ""


def extract_name(text: str) -> str:
    """
    Best-effort name extraction.
    Uses spaCy NER (PERSON entity) on the first ~200 chars if the model
    is available; otherwise falls back to 'first non-empty line' heuristic.
    """
    header = text.strip().split("\n")[0:5]
    header_text = "\n".join(header)

    if NLP is not None:
        doc = NLP(header_text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()

    # Fallback: first non-empty line that looks like a name
    # (short, no digits, no email/url)
    for line in header:
        line = line.strip()
        if (
            line
            and len(line.split()) <= 4
            and not any(char.isdigit() for char in line)
            and "@" not in line
            and "http" not in line
        ):
            return line
    return "Not found"


def extract_skills(text: str) -> list:
    """Keyword-match against SKILLS_DB (case-insensitive)."""
    text_lower = text.lower()
    found = set()
    for skill in SKILLS_DB:
        # word-boundary-ish match, handles multi-word skills too
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.add(skill)
    return sorted(found)


def _find_section_span(lines, section_keys):
    """
    Find the line range belonging to a section, based on header keywords.
    Returns (start_idx, end_idx) or None.
    """
    all_headers = [kw for kws in SECTION_HEADERS.values() for kw in kws]
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip().lower().rstrip(":")
        if stripped in section_keys:
            start = i + 1
            break
    if start is None:
        return None

    end = len(lines)
    for j in range(start, len(lines)):
        stripped = lines[j].strip().lower().rstrip(":")
        if stripped in all_headers and stripped not in section_keys:
            end = j
            break
    return (start, end)


def extract_section(text: str, section_name: str) -> str:
    """Extract raw text belonging to a named section (education/experience/etc.)."""
    lines = text.split("\n")
    keys = SECTION_HEADERS.get(section_name, [])
    span = _find_section_span(lines, keys)
    if not span:
        return ""
    start, end = span
    content = [l.strip() for l in lines[start:end] if l.strip()]
    return "\n".join(content)


# ---------------------------------------------------------------------
# 4. MAIN PARSE FUNCTION
# ---------------------------------------------------------------------

def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Full pipeline: extract -> clean -> parse fields.
    Returns a structured dict ready for JSON/CSV export.
    """
    raw_text = extract_text(file_bytes, filename)
    text = clean_text(raw_text)

    result = {
        "filename": filename,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_linkedin(text),
        "github": extract_github(text),
        "skills": extract_skills(text),
        "education": extract_section(text, "education"),
        "experience": extract_section(text, "experience"),
        "projects": extract_section(text, "projects"),
        "certifications": extract_section(text, "certifications"),
        "raw_text_length": len(text),
    }
    return result


def result_to_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Quick manual test hook — run: python resume_parser.py sample.pdf
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "rb") as f:
            data = f.read()
        parsed = parse_resume(data, path)
        print(result_to_json(parsed))
    else:
        print("Usage: python resume_parser.py <resume.pdf|resume.docx>")

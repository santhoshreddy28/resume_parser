# Smart Resume Parser

Extracts structured info — name, email, phone, LinkedIn/GitHub, skills,
education, experience, projects, certifications — from PDF/DOCX resumes,
with a Streamlit UI for upload, viewing, and CSV/JSON export.

## Project Structure

```
resume_parser/
├── app.py                # Streamlit UI
├── resume_parser.py       # Core parsing logic (importable + CLI)
├── requirements.txt
├── sample_resumes/        # 5 test resumes (3 DOCX, 2 PDF)
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

> Note: the app still works even if the spaCy model isn't downloaded —
> it falls back to a heuristic for name extraction — but installing the
> model gives noticeably better accuracy.

## Run the app

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501),
and upload one or more resumes from `sample_resumes/` to try it out.

## Run the parser from the command line

```bash
python resume_parser.py sample_resumes/resume_1_priya_sharma.docx
```

This prints the parsed result as JSON.

## How it works

1. **Extraction** — `PyMuPDF` (`fitz`) reads PDF text; `python-docx` reads DOCX
   paragraphs.
2. **Cleaning** — normalizes whitespace and line breaks.
3. **Field extraction**:
   - Email / phone / LinkedIn / GitHub via regex.
   - Name via spaCy's `PERSON` named-entity recognition (with a
     first-line heuristic fallback).
   - Skills via keyword matching against a curated tech-skills vocabulary.
   - Education / Experience / Projects / Certifications via section-header
     detection (splits the resume into blocks based on common headers).
4. **Output** — a Python dict, exportable to JSON or CSV, viewable in a
   Streamlit table or per-resume detail view.

## Possible extensions

- Swap keyword-matching skills extraction for a trained NER model to catch
  skills not in the vocabulary list.
- Use `dateparser` to normalize education/experience dates.
- Add resume-to-job-description match scoring (cosine similarity on TF-IDF).
- Deploy to Streamlit Community Cloud for a live demo link.

## Deliverables checklist (per internship guidelines)

- [x] Codebase (`resume_parser.py`, `app.py`)
- [x] UI app (Streamlit)
- [x] 5 test resumes (`sample_resumes/`)
- [x] Output files (CSV/JSON export from the app)

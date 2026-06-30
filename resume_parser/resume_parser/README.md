# Smart Resume Parser

Extracts structured information (name, contact details, skills, education,
experience) from PDF / DOCX resumes and presents it through an interactive
Streamlit app, with JSON/CSV export.

## Project Structure
```
resume_parser/
├── app/
│   ├── parser.py          # Core parsing engine (text extraction + NLP + regex)
│   └── streamlit_app.py   # Streamlit UI
├── samples/
│   ├── generate_samples.py
│   └── sample_*.pdf/docx  # 5 generated test resumes
├── outputs/
│   ├── parsed_resumes.json
│   └── parsed_resumes.csv
└── requirements.txt
```

## How It Works
1. **Text extraction** — `PyMuPDF` (fitz) reads PDF resumes, `python-docx`
   reads DOCX resumes (including tables, common in templated formats).
2. **Cleaning** — whitespace normalisation, blank-line removal.
3. **Section splitting** — resume text is split into Summary / Skills /
   Experience / Education / Projects / Certifications using a header-keyword
   lookup table.
4. **Contact info** — regex patterns for email, phone, LinkedIn, GitHub URLs.
   Name is inferred heuristically from the first capitalised short line.
5. **Skill extraction** — a `spaCy` `PhraseMatcher` matches against a curated
   ~70-term technical skill library (languages, frameworks, ML/data tools,
   cloud/DevOps). This uses spaCy's rule-based matching rather than the
   downloadable pretrained model, so it runs fully offline.
6. **Education / Experience** — regex (degree keywords, year-range patterns
   like `2022 - 2026`) plus line-grouping heuristics to cluster job titles
   with their bullet points.
7. **Output** — results as a Python dict / JSON, with CSV export for batch
   processing of multiple resumes at once.

## Setup
```bash
pip install -r requirements.txt
```

## Run the App
```bash
cd app
streamlit run streamlit_app.py
```
Then open the local URL Streamlit prints (default `http://localhost:8501`),
upload one or more PDF/DOCX resumes, and view parsed results per-tab with
JSON/CSV download buttons.

## Run the Parser from the Command Line
```bash
python app/parser.py samples/sample_1_priya_sharma.pdf
```

## Regenerate Sample Resumes
```bash
cd samples
python generate_samples.py
```

## Extending the Project
- Add a "resume score" feature comparing detected skills against a target
  job description (cosine similarity on TF-IDF vectors).
- Swap the rule-based skill matcher for spaCy's pretrained `en_core_web_sm`
  NER model if internet access to download it is available, for richer
  entity recognition (ORG, GPE, DATE).
- Add OCR fallback (`pytesseract` + `pdf2image`) for scanned/image-based
  resumes.

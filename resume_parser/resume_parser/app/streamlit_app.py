"""
Smart Resume Parser - Streamlit UI

Run with:  streamlit run streamlit_app.py
"""

import io
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    parse_resume_from_text,
)

st.set_page_config(page_title="Smart Resume Parser", page_icon="📄", layout="wide")

st.title("📄 Smart Resume Parser")
st.caption(
    "Upload a resume (PDF or DOCX) to automatically extract contact details, "
    "skills, education, and experience."
)

with st.sidebar:
    st.header("About")
    st.write(
        "This tool extracts structured information from resumes using "
        "**PyMuPDF** / **python-docx** for text extraction, and "
        "**spaCy** (rule-based PhraseMatcher) + **regex** for information extraction."
    )
    st.write("**Supported formats:** PDF, DOCX")
    st.divider()
    st.write("Built for the Internship Project Phase — Smart Resume Parser")

uploaded_files = st.file_uploader(
    "Upload one or more resumes",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

if uploaded_files:
    all_results = []

    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        suffix = Path(uploaded_file.name).suffix.lower()

        # Extract text directly from the in-memory bytes
        if suffix == ".pdf":
            import fitz
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                raw_text = "\n".join(page.get_text() for page in doc)
        else:
            import docx
            document = docx.Document(io.BytesIO(file_bytes))
            raw_text = "\n".join(p.text for p in document.paragraphs)

        result = parse_resume_from_text(raw_text, file_name=uploaded_file.name)
        all_results.append(result)

    st.success(f"Parsed {len(all_results)} resume(s) successfully.")

    tab_labels = [r["file_name"] for r in all_results]
    tabs = st.tabs(tab_labels)

    for tab, result in zip(tabs, all_results):
        with tab:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Contact Information")
                st.write(f"**Name:** {result['name'] or 'Not detected'}")
                st.write(f"**Email:** {result['email'] or 'Not detected'}")
                st.write(f"**Phone:** {result['phone'] or 'Not detected'}")
                st.write(f"**LinkedIn:** {result['linkedin'] or 'Not detected'}")
                st.write(f"**GitHub:** {result['github'] or 'Not detected'}")

                st.subheader("Skills")
                if result["skills"]:
                    st.write(" ".join(f"`{s}`" for s in result["skills"]))
                else:
                    st.write("No skills detected.")

                st.subheader("Summary")
                st.write(result["summary"] or "Not detected")

            with col2:
                st.subheader("Education")
                if result["education"]:
                    for edu in result["education"]:
                        st.write(f"- {edu['line']}")
                else:
                    st.write("Not detected")

                st.subheader("Experience")
                if result["experience"]:
                    for exp in result["experience"]:
                        st.markdown(f"**{exp['title_line']}**")
                        for b in exp["bullets"]:
                            st.write(f"  {b}")
                else:
                    st.write("Not detected")

            with st.expander("Raw JSON output"):
                st.json(result)

    st.divider()
    st.subheader("📦 Export Results")

    # JSON export (all resumes)
    json_bytes = json.dumps(all_results, indent=2).encode("utf-8")
    st.download_button(
        "⬇️ Download all results as JSON",
        data=json_bytes,
        file_name="parsed_resumes.json",
        mime="application/json",
    )

    # CSV export (flattened)
    rows = []
    for r in all_results:
        rows.append({
            "file_name": r["file_name"],
            "name": r["name"],
            "email": r["email"],
            "phone": r["phone"],
            "linkedin": r["linkedin"],
            "github": r["github"],
            "skills": ", ".join(r["skills"]),
            "education": " | ".join(e["line"] for e in r["education"]),
            "experience_titles": " | ".join(e["title_line"] for e in r["experience"]),
        })
    df = pd.DataFrame(rows)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download all results as CSV",
        data=csv_bytes,
        file_name="parsed_resumes.csv",
        mime="text/csv",
    )

    with st.expander("📊 View as table"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("👆 Upload resumes above to get started, or try the sample resumes included in the `samples/` folder.")

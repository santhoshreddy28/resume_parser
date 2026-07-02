"""
Smart Resume Parser — Streamlit App
Upload a PDF/DOCX resume and get structured info: contact details,
skills, education, experience, projects, certifications.
Supports batch upload and CSV/JSON export.
"""

import json
import io

import pandas as pd
import streamlit as st

from resume_parser import parse_resume, NLP

st.set_page_config(page_title="Smart Resume Parser", page_icon="📄", layout="wide")

st.title("📄 Smart Resume Parser")
st.caption("Upload one or more resumes (PDF/DOCX) to extract structured info automatically.")

if NLP is None:
    st.warning(
        "spaCy language model not found — name extraction is using a fallback heuristic. "
        "For best accuracy, run: `python -m spacy download en_core_web_sm`",
        icon="⚠️",
    )

uploaded_files = st.file_uploader(
    "Upload resumes",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

if uploaded_files:
    results = []
    with st.spinner(f"Parsing {len(uploaded_files)} resume(s)..."):
        for uf in uploaded_files:
            try:
                file_bytes = uf.read()
                parsed = parse_resume(file_bytes, uf.name)
                results.append(parsed)
            except Exception as e:
                st.error(f"Failed to parse {uf.name}: {e}")

    if results:
        st.success(f"Parsed {len(results)} resume(s) successfully.")

        tab1, tab2 = st.tabs(["📋 Table View", "🔍 Detailed View"])

        # ---------------- TABLE VIEW ----------------
        with tab1:
            table_rows = []
            for r in results:
                table_rows.append({
                    "File": r["filename"],
                    "Name": r["name"],
                    "Email": r["email"],
                    "Phone": r["phone"],
                    "LinkedIn": r["linkedin"],
                    "GitHub": r["github"],
                    "Skills": ", ".join(r["skills"]),
                })
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True)

            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv_bytes,
                    file_name="parsed_resumes.csv",
                    mime="text/csv",
                )
            with col2:
                json_bytes = json.dumps(results, indent=2, ensure_ascii=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download JSON",
                    data=json_bytes,
                    file_name="parsed_resumes.json",
                    mime="application/json",
                )

        # ---------------- DETAILED VIEW ----------------
        with tab2:
            for r in results:
                with st.expander(f"📄 {r['name']}  —  {r['filename']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Email:** {r['email'] or '—'}")
                        st.markdown(f"**Phone:** {r['phone'] or '—'}")
                        st.markdown(f"**LinkedIn:** {r['linkedin'] or '—'}")
                        st.markdown(f"**GitHub:** {r['github'] or '—'}")
                    with c2:
                        if r["skills"]:
                            st.markdown("**Skills:**")
                            st.write(", ".join(r["skills"]))
                        else:
                            st.markdown("**Skills:** Not detected")

                    st.markdown("---")
                    st.markdown("**🎓 Education**")
                    st.text(r["education"] or "Not found")

                    st.markdown("**💼 Experience**")
                    st.text(r["experience"] or "Not found")

                    st.markdown("**🚀 Projects**")
                    st.text(r["projects"] or "Not found")

                    if r["certifications"]:
                        st.markdown("**📜 Certifications**")
                        st.text(r["certifications"])

else:
    st.info("👆 Upload one or more PDF/DOCX resumes to get started. Sample resumes are in `sample_resumes/`.")

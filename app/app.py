"""Streamlit web UI for AI Lease Parser."""

import sys
import os
import io
import tempfile
from pathlib import Path

# Ensure src is importable when running from the app directory
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from src.pdf_reader import read_file
from src.extractor import extract, get_values, get_confidence_scores
from src.validator import validate
from src.exporter import export_csv, export_excel
from src.fields import LEASE_FIELDS, get_all_field_names


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Lease Parser",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("AI Lease Parser")
st.caption("Extract structured data from residential lease PDFs using OCR and AI.")


# ---------------------------------------------------------------------------
# Sidebar settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Settings")
    use_llm = st.checkbox(
        "Use LLM extraction (requires OPENAI_API_KEY)",
        value=False,
        help="Enable OpenAI-powered extraction for higher accuracy.",
    )
    show_confidence = st.checkbox("Show confidence scores", value=True)
    st.markdown("---")
    st.markdown("**About**")
    st.markdown("Drag and drop one or more lease PDFs to extract key fields.")
    st.markdown("You can edit fields before downloading.")


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload lease files (PDF or TXT)",
    type=["pdf", "txt"],
    accept_multiple_files=True,
    help="Drag and drop lease PDFs or text files here.",
)

if not uploaded_files:
    st.info("Upload one or more lease files to get started.")
    st.stop()


# ---------------------------------------------------------------------------
# Process files
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def process_uploaded_file(file_bytes: bytes, filename: str, use_llm: bool):
    """Cache processing results per file."""
    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        text = read_file(tmp_path)
        results = extract(text, use_llm=use_llm)
        values = get_values(results)
        confidence = get_confidence_scores(results)
        validation = validate(values)
        return values, confidence, validation, text
    finally:
        os.unlink(tmp_path)


all_records = []
tabs = st.tabs([f.name for f in uploaded_files])

for tab, uploaded_file in zip(tabs, uploaded_files):
    with tab:
        with st.spinner(f"Extracting data from {uploaded_file.name}..."):
            file_bytes = uploaded_file.read()
            values, confidence, validation, raw_text = process_uploaded_file(
                file_bytes, uploaded_file.name, use_llm
            )

        # Show validation status
        if validation["is_valid"]:
            st.success("Validation passed")
        else:
            for err in validation["errors"]:
                st.error(err)

        if validation["warnings"]:
            for warn in validation["warnings"]:
                st.warning(warn)

        # Editable fields table
        st.subheader("Extracted Fields")
        st.caption("Edit any field before downloading.")

        edited_values = {}
        cols = st.columns(2)

        for i, field_name in enumerate(get_all_field_names()):
            col = cols[i % 2]
            raw_val = values.get(field_name)
            conf = confidence.get(field_name, 0.0)
            field_info = LEASE_FIELDS[field_name]

            label = field_name.replace("_", " ").title()
            if show_confidence and conf > 0:
                label += f" ({conf:.0%})"

            if raw_val is None:
                display_val = ""
            elif isinstance(raw_val, list):
                display_val = "; ".join(str(v) for v in raw_val)
            else:
                display_val = str(raw_val)

            help_text = field_info["description"]
            if not field_info["required"]:
                help_text += " (optional)"

            edited = col.text_input(
                label,
                value=display_val,
                key=f"{uploaded_file.name}_{field_name}",
                help=help_text,
            )
            edited_values[field_name] = edited if edited else None

        edited_values["_source"] = uploaded_file.name
        all_records.append(edited_values)

        # Show raw text expander
        with st.expander("View raw extracted text"):
            st.text(raw_text[:3000] + ("..." if len(raw_text) > 3000 else ""))


# ---------------------------------------------------------------------------
# Download section
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Download Results")

col1, col2 = st.columns(2)

with col1:
    if st.button("Generate CSV"):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            csv_path = tmp.name
        export_csv(all_records, csv_path)
        csv_data = Path(csv_path).read_bytes()
        os.unlink(csv_path)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="lease_data.csv",
            mime="text/csv",
        )

with col2:
    if st.button("Generate Excel"):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            xlsx_path = tmp.name
        export_excel(all_records, xlsx_path)
        xlsx_data = Path(xlsx_path).read_bytes()
        os.unlink(xlsx_path)
        st.download_button(
            label="Download Excel",
            data=xlsx_data,
            file_name="lease_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

if all_records:
    st.markdown("---")
    st.subheader("Summary Table")
    display_records = [
        {k: v for k, v in r.items() if k != "_source"} for r in all_records
    ]
    df = pd.DataFrame(display_records)
    st.dataframe(df, use_container_width=True)

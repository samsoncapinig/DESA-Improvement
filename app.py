# =============================
# IMPORTS
# =============================
import streamlit as st
import pandas as pd
import numpy as np
import re
import os
from collections import defaultdict
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import tempfile
import google.generativeai as genai

# ✅ Gemini setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-3-flash-preview")


# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="SDO Masbate City Project DESA", layout="wide")

st.image("logo.png", width=1200)
st.title("SDO Masbate City Project DESA")
st.markdown("Designed for faster data analysis and interpretation of evaluation results.")

# =============================
# CONSTANTS
# =============================
EXCLUDED_CATEGORIES = ["response", "department", "submitted on:", "Course", "group", "ID", "Full name", "Username", "institution",]

QUAL_HEADER_PATTERNS = {
    "Insights": r"^Q\d+[_\- ]*Insights$",
    "Most Significant Learning": r"^Q\d+[_\- ]*Most[ _\-]*Significant[ _\-]*Learning$",
    "Learnings": r"^Q\d+[_\- ]*Learnings?$",
    "Suggestions": r"^Q\d+[_\- ]*Suggestions?$"
}

# =============================
# HELPERS
# =============================
def load_any_file(uploaded_file):
    try:
        return pd.read_excel(uploaded_file, engine="openpyxl")
    except:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)

def detect_rating_columns(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return [c for c in numeric_cols if "id" not in c.lower()]

def extract_category(col):
    return col.split("->")[0].strip()

def detect_strict_qualitative_columns(df):
    found = defaultdict(list)
    for col in df.columns:
        for label, pattern in QUAL_HEADER_PATTERNS.items():
            if re.match(pattern, col.strip(), flags=re.IGNORECASE):
                found[label].append(col)
    return found


import google.generativeai as genai

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-3-flash-preview")

def generate_summary(text_list):
    combined_text = "\n---\n".join(text_list[:50])  # limit for safety

    prompt = (
        "Summarize the following survey responses into 3 to 5 concise themes. "
        "Each theme should be written as a short bullet point (1–2 sentences only). "
        "Include direct quotation from the responses if possible. "
        "Do not include subcategories, analysis, or explanations.\n\n"
        f"Responses:\n{combined_text}"
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"


# --- Streamlit UI ---
st.title("📝 Qualitative Response Summarizer")
st.write("Upload a CSV file containing open-ended responses to generate an AI summary.")

# =============================
# FORM 5
# =============================

def generate_form5_pdf(combined_df, overall_rating):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    # TITLE
    content.append(Paragraph("RV-QAME TOOL-05", styles["Heading2"]))
    content.append(Paragraph("Overall Monitoring & Evaluation Results Form", styles["Title"]))

    # TRAINING INFO (you can customize these)
    content.append(Paragraph("<b>Title of Training Program:</b> Project DESA", styles["Normal"]))
    content.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))

    # TABLE HEADER
    table_data = [[
        "Learning Area",
        "Daily Eval",
        "End Program Eval",
        "Overall Result"
    ]]

    for idx, row in combined_df.iterrows():
        rating = f"{row['Average Rating']:.2f}"
        table_data.append([idx, rating, rating, rating])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    content.append(table)

    # ANALYSIS
    content.append(Paragraph("<b>Analysis:</b>", styles["Heading3"]))
    content.append(Paragraph("Overall performance is satisfactory based on evaluation results.", styles["Normal"]))

    # RECOMMENDATION
    content.append(Paragraph("<b>Recommendations:</b>", styles["Heading3"]))
    content.append(Paragraph("Enhance delivery strategies and provide more support materials.", styles["Normal"]))

    doc.build(content)
    return temp_file.name

# =============================
# FORM 4
# =============================
def generate_form4_pdf(combined_df, qualitative_results, overall_rating):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    # HEADER
    content.append(Paragraph("RV-QAME TOOL-04", styles["Heading2"]))
    content.append(Paragraph("Monitoring and Evaluation Analysis Form", styles["Title"]))

    # TRAINING INFO
    content.append(Paragraph("<b>Title of Training Program:</b> Project DESA", styles["Normal"]))
    content.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))

    # =============================
    # SECTION 1: SESSION EVALUATION
    # =============================
    content.append(Paragraph("<b>1. Session Evaluation</b>", styles["Heading2"]))

    table_data = [["Category", "Rating"]]

    for idx, row in combined_df.iterrows():
        table_data.append([idx, f"{row['Average Rating']:.2f}"])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    content.append(table)

    # =============================
    # QUALITATIVE SUMMARY
    # =============================
    for label, responses in qualitative_results.items():
        content.append(Paragraph(f"<b>{label}</b>", styles["Heading2"]))

        summary = generate_summary(responses)

        content.append(Paragraph(summary, styles["Normal"]))

    # =============================
    # FINDINGS
    # =============================
    content.append(Paragraph("<b>Major Observations / Findings:</b>", styles["Heading2"]))
    content.append(Paragraph("Participants generally showed positive engagement.", styles["Normal"]))

    # =============================
    # OVERALL RATING
    # =============================
    content.append(Paragraph(f"<b>Overall Rating:</b> {overall_rating:.2f}", styles["Heading2"]))

    # =============================
    # RECOMMENDATIONS
    # =============================
    content.append(Paragraph("<b>Recommendations:</b>", styles["Heading2"]))
    content.append(Paragraph("Improve pacing and provide additional hands-on activities.", styles["Normal"]))

    doc.build(content)
    return temp_file.name

st.subheader("📄 Generate Reports")

col1, col2 = st.columns(2)

with col1:
    if uploaded_files and category_results:

    combined_df = pd.DataFrame(category_results)
    combined_df["Average Rating"] = combined_df.mean(axis=1)

    st.dataframe(combined_df)

    overall_rating = combined_df['Average Rating'].mean()

    # =============================
    # PDF BUTTONS ✅ INSIDE BLOCK
    # =============================
    st.subheader("📄 Generate Reports")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Download Form 4 (Detailed Report)"):
            file_path = generate_form4_pdf(
                combined_df,
                qualitative_results,
                overall_rating
            )
            with open(file_path, "rb") as f:
                st.download_button(
                    "Click to Download Form 4",
                    f,
                    "Form4_Report.pdf"
                )

    with col2:
        if st.button("Download Form 5 (Summary Report)"):
            file_path = generate_form5_pdf(
                combined_df,
                overall_rating
            )
            with open(file_path, "rb") as f:
                st.download_button(
                    "Click to Download Form 5",
                    f,
                    "Form5_Report.pdf"
                )
# =============================
# FILE UPLOADER
# =============================
uploaded_files = st.file_uploader(
    "Upload evaluation files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

category_results = {}
qualitative_results = defaultdict(list)

# =============================
# PROCESS FILES
# =============================
if uploaded_files:
    for f in uploaded_files:
        df = load_any_file(f)
        st.success(f"Loaded {f.name}")

        rating_cols = detect_rating_columns(df)
        if rating_cols:
            cat_df = pd.DataFrame({
                "Category": [extract_category(c) for c in rating_cols],
                "Rating": [df[c].mean() for c in rating_cols]
            })

            cat_df = cat_df[~cat_df["Category"].str.lower().isin(EXCLUDED_CATEGORIES)]
            cat_avg = cat_df.groupby("Category", as_index=False).mean()

            category_results[f.name] = cat_avg.set_index("Category")["Rating"]

        qual_map = detect_strict_qualitative_columns(df)
        for label, cols in qual_map.items():
            for col in cols:
                qualitative_results[label].extend(df[col].dropna().astype(str).tolist())

    # =============================
    # COMBINED TABLE
    # =============================
    st.subheader("📊 Combined Category Ratings")

    combined_df = pd.DataFrame(category_results)
    combined_df["Average Rating"] = combined_df.mean(axis=1)

    st.dataframe(combined_df, use_container_width=True)

    st.markdown(f"### ✅ Overall Rating: {combined_df['Average Rating'].mean():.2f}")

    # =============================
    # QUALITATIVE RESPONSES
    # =============================
    st.subheader("📝 Qualitative Responses")

    for label, responses in qualitative_results.items():
        if responses:
            st.markdown(f"### {label}")
            st.dataframe(pd.DataFrame({label: responses}))

            if st.button(f"Analyze {label}", key=label):
                with st.spinner("Analyzing..."):
                    result = generate_summary(responses)

                st.markdown("#### 🤖 Thematic Analysis")
                st.write(result)
    


from datetime import datetime

st.divider()

col_pic, col_text = st.columns([1, 6])

with col_pic:
    st.image("samson.png", width=80)

with col_text:
    st.markdown(
        f"""
        **Developed by Sir Sam**   
        Project DESA • SDO Masbate City  
        © {datetime.now().year} . All rights reserved.
        """
    )



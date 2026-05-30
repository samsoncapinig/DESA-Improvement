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
from openai import OpenAI

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
                    result = get_themes(label, responses)

                st.markdown("#### 🤖 Thematic Analysis")
                st.write(result)

# =============================
# FOOTER
# =============================
st.divider()

col1, col2 = st.columns([1, 6])

with col1:
    st.image("samson.png", width=80)

with col2:
    st.markdown(f"""
    **Developed by Sir Sam**  
    © {datetime.now().year}
    """)

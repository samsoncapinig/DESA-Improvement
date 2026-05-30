# =============================
# FILE UPLOADER
# =============================
uploaded_files = st.file_uploader(
    "Upload evaluation files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

# =============================
# PROCESS FILES
# =============================
if uploaded_files:
    category_results = {}
    qualitative_results = defaultdict(list)

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
                qualitative_results[label].extend(
                    df[col].dropna().astype(str).tolist()
                )

    # =============================
    # COMBINED TABLE
    # =============================
    if category_results:
        st.subheader("📊 Combined Category Ratings")

        combined_df = pd.DataFrame(category_results)
        combined_df["Average Rating"] = combined_df.mean(axis=1)

        st.dataframe(combined_df, use_container_width=True)

        overall_rating = combined_df["Average Rating"].mean()
        st.markdown(f"### ✅ Overall Rating: {overall_rating:.2f}")

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

        # =============================
        # PDF REPORTS ✅ FIXED
        # =============================
        st.subheader("📄 Generate Reports")

        col1, col2 = st.columns(2)

        # FORM 4
        with col1:
            file_path_4 = generate_form4_pdf(
                combined_df,
                qualitative_results,
                overall_rating
            )
            with open(file_path_4, "rb") as f:
                st.download_button(
                    "📄 Download Form 4 (Detailed Report)",
                    f,
                    "Form4_Report.pdf"
                )

        # FORM 5
        with col2:
            file_path_5 = generate_form5_pdf(
                combined_df,
                overall_rating
            )
            with open(file_path_5, "rb") as f:
                st.download_button(
                    "📄 Download Form 5 (Summary Report)",
                    f,
                    "Form5_Report.pdf"
                )

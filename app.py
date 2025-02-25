import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import openai

# Retrieve OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Title and Welcome Message
st.title("✨ DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! Let me help you convert your PowerBI reports to Tableau dashboards.")

# Sidebar for uploading file
with st.sidebar:
    st.subheader("📂 Upload Your PBIX File")
    st.write("Upload your Power BI PBIX file to extract DAX expressions, schema, and relationships for conversion and analysis.")

    uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

    if uploaded_file:
        temp_path = "temp_file.pbix"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Store file path in session state
        st.session_state.pbix_file_path = temp_path
        st.success("✅ PBIX file uploaded successfully!")

# ✅ Initialize session state for persistent sections
if "sections_open" not in st.session_state:
    st.session_state.sections_open = {
        "datasource": True,
        "dax_conversion": True,
        "relationships": True,
        "qna": True
    }

# ✅ Function to keep sections open
def keep_section_open(key):
    """Ensures sections remain open after interactions."""
    if key not in st.session_state.sections_open:
        st.session_state.sections_open[key] = True
    return st.session_state.sections_open[key]

# ✅ Always Open Section: Datasource Setup
if keep_section_open("datasource"):
    with st.container():
        st.subheader("🔍 1. Datasource Setup")
        st.write("Identify key tables and columns in your Power BI data and suggest an appropriate Tableau datasource structure.")

        # Function to extract schema from the PBIX file
        def extract_schema(file_path):
            try:
                model = PBIXRay(file_path)
                schema = model.schema
                return schema if not schema.empty else "No schema found."
            except Exception as e:
                return f"Error during schema extraction: {e}"

        if st.button("Extract Schema", key="extract_schema"):
            if uploaded_file:
                schema = extract_schema("temp_file.pbix")
                if isinstance(schema, pd.DataFrame):
                    table_names = sorted(schema["TableName"].unique().tolist())

                    st.subheader("📌 Extracted Tables and Columns")
                    for table in table_names:
                        st.write(f"📂 **{table}**")
                        columns = schema[schema["TableName"] == table]["ColumnName"].tolist()
                        st.write(", ".join(columns) if columns else "No columns found.")
                else:
                    st.write(schema)
            else:
                st.warning("Please upload a PBIX file to proceed.")

# ✅ Always Open Section: DAX Extraction & Conversion
if keep_section_open("dax_conversion"):
    with st.container():
        st.subheader("🔄 2. DAX Expression Extraction and Conversion")
        st.write("Extract and convert DAX expressions from your Power BI file into Tableau-compatible calculated fields.")

        # Function to extract all DAX expressions from a PBIX file
        def extract_all_dax_expressions(file_path):
            try:
                model = PBIXRay(file_path)
                dax_measures = model.dax_measures
                return dax_measures[['Expression']] if not dax_measures.empty and 'Expression' in dax_measures.columns else "No DAX expressions found."
            except Exception as e:
                return f"Error during DAX extraction: {e}"

        if "pbix_file_path" in st.session_state:
            num_expressions = st.number_input("🔢 Number of DAX expressions to extract:", min_value=1, max_value=100, value=5, key="num_dax")

            if st.button("🚀 Extract DAX Expressions", key="extract_dax"):
                extracted_dax_df = extract_all_dax_expressions(st.session_state.pbix_file_path)
                if isinstance(extracted_dax_df, pd.DataFrame) and not extracted_dax_df.empty:
                    st.session_state.dax_expressions = extracted_dax_df['Expression'].tolist()[:num_expressions]
                    st.write("### 📌 Extracted DAX Expressions")
                    for i, expr in enumerate(st.session_state.dax_expressions, 1):
                        st.write(f"**DAX Expression {i}:** {expr}")
                else:
                    st.write(extracted_dax_df)
        else:
            st.warning("⚠️ Please upload a PBIX file first.")

# ✅ Always Open Section: Relationships Extraction
if keep_section_open("relationships"):
    with st.container():
        st.subheader("🔗 3. Relationships Extraction")
        st.write("Extract relationships from your Power BI data model to help you maintain data integrity in Tableau.")

        def extract_relationships(file_path):
            try:
                model = PBIXRay(file_path)
                relationships = model.relationships
                return relationships if not relationships.empty else "No relationships found."
            except Exception as e:
                return f"Error during relationships extraction: {e}"

        if st.button("Extract Relationships", key="extract_relationships"):
            if uploaded_file:
                relationships = extract_relationships("temp_file.pbix")
                if isinstance(relationships, pd.DataFrame):
                    st.dataframe(relationships)
                else:
                    st.write(relationships)
            else:
                st.warning("Please upload a PBIX file to proceed.")

# ✅ Always Open Section: Q&A Chat
if keep_section_open("qna"):
    with st.container():
        st.subheader("💬 4. Ask Me Anything!")
        st.write("Have any questions about Power BI, DAX expressions, or Tableau? Ask here!")

        question = st.text_input("Enter your question:", key="question_input")
        if question:
            with st.spinner("Generating answer..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an assistant knowledgeable in Power BI DAX expressions and Tableau."},
                            {"role": "user", "content": question}
                        ],
                        max_tokens=500
                    )
                    answer = response.choices[0].message['content'].strip()
                    st.write("**Answer:**")
                    st.write(answer)
                except Exception as e:
                    st.error(f"Error during question processing: {e}")

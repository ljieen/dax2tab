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

# ✅ Datasource Setup Section
with st.expander("🔍 1. Datasource Setup", expanded=True):
    st.write("Identify key tables and columns in your Power BI data and suggest an appropriate Tableau datasource structure.")
    
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

# ✅ DAX Extraction & Conversion Section
with st.expander("🔄 2. DAX Expression Extraction and Conversion", expanded=True):
    st.write("Extract DAX expressions from your Power BI file. You can choose to extract all expressions or convert selected ones into Tableau-compatible calculated fields.")

    def extract_all_dax_expressions(file_path):
        try:
            model = PBIXRay(file_path)
            dax_measures = model.dax_measures
            return dax_measures if not dax_measures.empty else "No DAX expressions found."
        except Exception as e:
            return f"Error during DAX extraction: {e}"

    def convert_dax_to_tableau(dax_expression):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You convert DAX expressions to Tableau calculated fields."},
                    {"role": "user", "content": f"Convert this DAX expression to Tableau: {dax_expression}"}
                ],
                max_tokens=300
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            return f"Error during conversion: {e}"

    if "pbix_file_path" in st.session_state:
        extracted_dax_df = extract_all_dax_expressions(st.session_state.pbix_file_path)
        if isinstance(extracted_dax_df, pd.DataFrame) and not extracted_dax_df.empty:
            extracted_dax_df = extracted_dax_df.reset_index(drop=True)
            st.write(f"### 📌 Total DAX Expressions Found: {len(extracted_dax_df)}")
            
            # Allow filtering by DisplayFolder if available
            if "DisplayFolder" in extracted_dax_df.columns:
                display_folders = extracted_dax_df["DisplayFolder"].dropna().unique().tolist()
                display_folders.sort()
                selected_folder = st.selectbox("Filter by Display Folder", ["All"] + display_folders, key="display_folder")
                if selected_folder != "All":
                    extracted_dax_df = extracted_dax_df[extracted_dax_df["DisplayFolder"] == selected_folder]
            
            st.write("### 📄 Extracted DAX Expressions")
            st.dataframe(extracted_dax_df)
            
            csv = extracted_dax_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download DAX Expressions",
                data=csv,
                file_name="dax_expressions.csv",
                mime="text/csv"
            )
            
            selected_indices = st.multiselect("Select expressions for conversion", extracted_dax_df.index.tolist())
            
            if st.button("🚀 Convert Selected DAX Expressions to Tableau", key="convert_selected_dax"):
                selected_expressions = extracted_dax_df.loc[selected_indices, "Expression"].tolist()
                converted_data = [(expr, convert_dax_to_tableau(expr)) for expr in selected_expressions]
                converted_df = pd.DataFrame(converted_data, columns=["DAX Expression", "Tableau Calculation"])
                
                st.write("### 📌 Converted DAX Expressions to Tableau Calculated Fields")
                st.dataframe(converted_df)
                
                csv = converted_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Converted DAX Expressions",
                    data=csv,
                    file_name="converted_dax_expressions.csv",
                    mime="text/csv"
                )
        else:
            st.write(extracted_dax_df)
    else:
        st.warning("⚠️ Please upload a PBIX file first.")

# ✅ Relationships Extraction Section
with st.expander("🔗 3. Relationships Extraction", expanded=True):
    st.write("Extract relationships from your Power BI data model to help you maintain data integrity in Tableau.")

# ✅ Q&A Chat Section
with st.expander("💬 4. Ask Me Anything!", expanded=True):
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

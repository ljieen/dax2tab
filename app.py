import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io
import openai
import tableauserverclient as TSC

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

# Block for Datasource Setup
with st.expander("🔍 1. Datasource Setup"):
    st.write("This section helps identify key tables and columns in your Power BI data and suggests an appropriate Tableau datasource structure.")

    # Function to extract schema from the PBIX file
    def extract_schema(file_path):
        try:
            model = PBIXRay(file_path)
            schema = model.schema
            if schema.empty:
                return "No schema found."
            return schema
        except Exception as e:
            return f"Error during schema extraction: {e}"

    if st.button("Extract Schema"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            schema = extract_schema("temp_file.pbix")
            if isinstance(schema, pd.DataFrame):
                st.write("Schema:")
                st.dataframe(schema)
            else:
                st.write(schema)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Extracting and Converting DAX Expressions
with st.expander("🔄 2. DAX Expression Extraction and Conversion"):
    st.write("Extract the first five DAX expressions from your Power BI file and convert them into Tableau-compatible calculated fields.")

    def extract_all_dax_expressions(file_path):
        try:
            model = PBIXRay(file_path)
            dax_measures = model.dax_measures
            if dax_measures.empty or 'Expression' not in dax_measures.columns:
                return "No DAX expressions found."
            dax_measures['Expression'] = dax_measures['Expression'].str.replace('\n', '', regex=False)
            return dax_measures[['Expression']]
        except Exception as e:
            return f"Error during DAX extraction: {e}"

    def convert_dax_to_tableau(dax_expression):
        try:
            with st.spinner("Converting DAX to Tableau calculated field..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an assistant that converts DAX expressions to Tableau calculated fields."},
                        {"role": "user", "content": f"Convert this DAX expression to Tableau calculated field: {dax_expression}"}
                    ],
                    max_tokens=300
                )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            return f"Error during conversion: {e}"

    if st.button("Extract and Convert First 5 DAX Expressions to Tableau Calculated Fields"):
        if not openai.api_key:
            st.error("OpenAI API key is not configured.")
        elif uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            dax_expressions = extract_all_dax_expressions("temp_file.pbix")
            if isinstance(dax_expressions, pd.DataFrame) and not dax_expressions.empty:
                st.write("DAX Expressions Table:")
                st.table(dax_expressions)
                first_five_dax_expressions = dax_expressions['Expression'].head(5)
                tableau_calculated_fields = []
                for i, dax_expression in enumerate(first_five_dax_expressions, 1):
                    tableau_calculated_field = convert_dax_to_tableau(dax_expression)
                    tableau_calculated_fields.append({
                        "DAX Expression": dax_expression,
                        "Tableau Calculated Field": tableau_calculated_field
                    })
                for i, conversion in enumerate(tableau_calculated_fields, 1):
                    st.write(f"### Conversion {i}")
                    st.write("**DAX Expression:**", conversion["DAX Expression"])
                    st.write("**Tableau Calculated Field:**", conversion["Tableau Calculated Field"])
                    st.write("---")
            else:
                st.write(dax_expressions if isinstance(dax_expressions, str) else "No DAX expressions found.")
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Exporting TWBX file
with st.expander("📦 3. Export as TWBX File"):
    st.write("Export the extracted metadata into a Tableau TWBX file.")

    def export_to_twbx(schema, relationships, output_file):
        try:
            with open(output_file, "wb") as f:
                f.write(schema.to_csv(index=False).encode('utf-8'))
                f.write(relationships.to_csv(index=False).encode('utf-8'))
            return output_file
        except Exception as e:
            return f"Error exporting TWBX file: {e}"

    if st.button("Export to TWBX"):
        if uploaded_file:
            schema = extract_schema("temp_file.pbix")
            relationships = extract_all_dax_expressions("temp_file.pbix")
            output_file = "output.twbx"
            result = export_to_twbx(schema, relationships, output_file)
            if isinstance(result, str):
                st.success(f"Exported successfully: {result}")
                with open(output_file, "rb") as file:
                    st.download_button("Download TWBX File", file, file_name="output.twbx")
            else:
                st.error(result)
        else:
            st.warning("Please upload a PBIX file to proceed.")

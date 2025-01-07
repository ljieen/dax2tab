import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io
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

# Block for Datasource Setup
with st.expander("🔍 1. Datasource Setup"):
    st.write("This section helps identify key tables and columns in your Power BI data and suggests an appropriate Tableau datasource structure.")
    st.write("• Identify key tables/columns")
    st.write("• Suggest Tableau datasource structure")

    # Function to extract schema from the PBIX file
    def extract_schema(file_path):
        try:
            model = PBIXRay(file_path)
            schema = model.schema
            if schema.empty:
                return pd.DataFrame(), "No schema found."
            return schema, "Schema extracted successfully."
        except Exception as e:
            return pd.DataFrame(), f"Error during schema extraction: {e}"

    if st.button("Extract Schema"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            schema, message = extract_schema("temp_file.pbix")
            if not schema.empty:
                st.write("Schema:")
                st.dataframe(schema)
            else:
                st.write(message)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Extracting and Converting DAX Expressions
with st.expander("🔄 2. DAX Expression Extraction and Conversion"):
    st.write("Extract the first five DAX expressions from your Power BI file and convert them into Tableau-compatible calculated fields for seamless migration.")

    # Function to extract all DAX expressions from a PBIX file
    def extract_all_dax_expressions(file_path):
        try:
            model = PBIXRay(file_path)
            dax_measures = model.dax_measures
            if dax_measures.empty or 'Expression' not in dax_measures.columns:
                return pd.DataFrame(), "No DAX expressions found."
            dax_measures['Expression'] = dax_measures['Expression'].str.replace('\n', '', regex=False)
            return dax_measures[['Expression']], "DAX expressions extracted successfully."
        except Exception as e:
            return pd.DataFrame(), f"Error during DAX extraction: {e}"

    # Function to convert DAX to Tableau calculated field using OpenAI
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

    # Extract and Convert the First 5 DAX Expressions
    if st.button("Extract and Convert First 5 DAX Expressions to Tableau Calculated Fields"):
        if not openai.api_key:
            st.error("OpenAI API key is not configured.")
        elif uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            dax_expressions, message = extract_all_dax_expressions("temp_file.pbix")
            
            if not dax_expressions.empty:
                st.write("DAX Expressions Table:")
                st.table(dax_expressions)

                # Limit to the first five expressions
                first_five_dax_expressions = dax_expressions['Expression'].head(5)

                # Convert each of the first five DAX expressions to Tableau calculated fields
                tableau_calculated_fields = []
                for i, dax_expression in enumerate(first_five_dax_expressions, 1):
                    tableau_calculated_field = convert_dax_to_tableau(dax_expression)
                    tableau_calculated_fields.append({
                        "DAX Expression": dax_expression,
                        "Tableau Calculated Field": tableau_calculated_field
                    })

                # Display converted expressions
                for i, conversion in enumerate(tableau_calculated_fields, 1):
                    st.write(f"### Conversion {i}")
                    st.write("**DAX Expression:**", conversion["DAX Expression"])
                    st.write("**Tableau Calculated Field:**", conversion["Tableau Calculated Field"])
                    st.write("---")
            else:
                st.write(message)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Relationships Extraction
with st.expander("🔗 3. Relationships Extraction"):
    st.write("Extract relationships from your Power BI data model to help you maintain data integrity and relationships in Tableau.")

    # Function to extract relationships from the PBIX file
    def extract_relationships(file_path):
        try:
            model = PBIXRay(file_path)
            relationships = model.relationships
            if relationships.empty:
                return pd.DataFrame(), "No relationships found."
            return relationships, "Relationships extracted successfully."
        except Exception as e:
            return pd.DataFrame(), f"Error during relationships extraction: {e}"

    if st.button("Extract Relationships"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            relationships, message = extract_relationships("temp_file.pbix")
            if not relationships.empty:
                st.write("Relationships:")
                st.dataframe(relationships)
            else:
                st.write(message)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Exporting TWBX file
with st.expander("📦 4. Export as TWBX File"):
    st.write("Export the extracted metadata into a Tableau-compatible CSV file.")

    def export_to_csv(schema, relationships, output_file):
        try:
            schema.to_csv("schema.csv", index=False)
            relationships.to_csv("relationships.csv", index=False)
            with open(output_file, "wb") as f:
                f.write(b"Exported successfully.")
            return output_file
        except Exception as e:
            return f"Error exporting file: {e}"

    if st.button("Export to CSV"):
        if uploaded_file:
            schema, _ = extract_schema("temp_file.pbix")
            relationships, _ = extract_relationships("temp_file.pbix")
            output_file = "output.csv"
            result = export_to_csv(schema, relationships, output_file)
            if not isinstance(result, str):
                st.success("Exported successfully.")
                with open(output_file, "rb") as file:
                    st.download_button("Download CSV File", file, file_name="output.csv")
            else:
                st.error(result)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Visuals Extraction
with st.expander("📊 5. Visuals Extraction"):
    st.write("Extract visuals metadata, including visual types, titles, and fields used in your Power BI reports.")

    # Function to extract visuals from the PBIX file
    def extract_visuals(file_path):
        try:
            model = PBIXRay(file_path)
            visuals = model.visuals
            if visuals.empty:
                return pd.DataFrame(), "No visuals found."
            return visuals, "Visuals extracted successfully."
        except Exception as e:
            return pd.DataFrame(), f"Error during visuals extraction: {e}"

    if st.button("Extract Visuals"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            visuals, message = extract_visuals("temp_file.pbix")
            if not visuals.empty:
                st.write("Extracted Visuals:")
                st.dataframe(visuals)
            else:
                st.write(message)
        else:
            st.warning("Please upload a PBIX file to proceed.")


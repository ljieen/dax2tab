import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io
import openai
import zipfile
import os
import xml.etree.ElementTree as ET

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
    st.write("Extract the first five DAX expressions from your Power BI file and convert them into Tableau-compatible calculated fields for seamless migration.")

    # Function to extract all DAX expressions from a PBIX file
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
            dax_expressions = extract_all_dax_expressions("temp_file.pbix")
            
            if isinstance(dax_expressions, pd.DataFrame) and not dax_expressions.empty:
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
                st.write(dax_expressions if isinstance(dax_expressions, str) else "No DAX expressions found.")
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
                return "No relationships found."
            return relationships
        except Exception as e:
            return f"Error during relationships extraction: {e}"

    if st.button("Extract Relationships"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            relationships = extract_relationships("temp_file.pbix")
            if isinstance(relationships, pd.DataFrame):
                st.write("Relationships:")
                st.dataframe(relationships)
            else:
                st.write(relationships)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for TWBX Generation
with st.expander("📦 4. Generate TWBX File"):
    st.write("Generate a Tableau TWBX file with extracted schema and calculated fields.")

    def create_twb_xml(schema, calculated_fields):
        workbook = ET.Element('workbook')
        datasources = ET.SubElement(workbook, 'datasources')
        datasource = ET.SubElement(datasources, 'datasource', attrib={"name": "ConvertedDataSource"})

        for _, row in schema.iterrows():
            ET.SubElement(datasource, 'column', attrib={"name": row['Name'], "type": row['Type']})

        for calc_field in calculated_fields:
            ET.SubElement(datasource, 'calculation', attrib={"name": calc_field['Name'], "formula": calc_field['Formula']})

        return ET.tostring(workbook, encoding='utf-8', method='xml')

    def create_twbx_file(schema, calculated_fields):
        twb_content = create_twb_xml(schema, calculated_fields)
        os.makedirs('output', exist_ok=True)
        twb_path = os.path.join('output', 'converted_workbook.twb')
        with open(twb_path, 'wb') as f:
            f.write(twb_content)

        twbx_path = os.path.join('output', 'converted_workbook.twbx')
        with zipfile.ZipFile(twbx_path, 'w') as zf:
            zf.write(twb_path, os.path.basename(twb_path))
        return twbx_path

    if st.button("Generate TWBX File"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            model = PBIXRay("temp_file.pbix")
            schema = model.schema
            dax_measures = model.dax_measures

            calculated_fields = []
            for i, dax in dax_measures[['Expression']].head(5).iterrows():
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Convert DAX expressions to Tableau calculated fields."},
                        {"role": "user", "content": f"Convert this DAX expression: {dax['Expression']}"}
                    ],
                    max_tokens=300
                )
                formula = response.choices[0].message['content'].strip()
                calculated_fields.append({"Name": f"Field_{i+1}", "Formula": formula})

            twbx_path = create_twbx_file(schema, calculated_fields)
            with open(twbx_path, 'rb') as f:
                st.download_button("Download TWBX File", f, file_name='converted_workbook.twbx')
        else:
            st.warning("Please upload a PBIX file first.")

# Block for Q&A Section with ChatGPT
with st.expander("💬 5. Ask Me Anything!"):
    st.write("Have any questions about Power BI, DAX expressions, or Tableau? Ask here, and I'll do my best to help you!")

    question = st.text_input("Enter your question about Power BI DAX expressions or Tableau:")
    if question:
        with st.spinner("Generating answer..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an assistant knowledgeable in Power BI DAX expressions and Tableau."},
                        {"role": "user", "content": question}

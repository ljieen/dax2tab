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
    st.subheader("👤 Upload Your PBIX File")
    uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

# Function to create TWB XML structure
def create_twb_xml(schema, calculated_fields):
    workbook = ET.Element('workbook')
    datasources = ET.SubElement(workbook, 'datasources')

    # Create a datasource element
    datasource = ET.SubElement(datasources, 'datasource', attrib={"name": "ConvertedDataSource"})
    for _, row in schema.iterrows():
        ET.SubElement(datasource, 'column', attrib={"name": row['Name'], "type": row['Type']})

    # Add calculated fields
    for calc_field in calculated_fields:
        calc = ET.SubElement(datasource, 'calculation', attrib={"name": calc_field['Name'], "formula": calc_field['Formula']})

    return ET.tostring(workbook, encoding='utf-8', method='xml')

# Function to create TWBX file
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

# Extract Schema
if uploaded_file:
    with open("temp_file.pbix", "wb") as f:
        f.write(uploaded_file.getbuffer())

    model = PBIXRay("temp_file.pbix")
    schema = model.schema
    dax_measures = model.dax_measures

    if not schema.empty and not dax_measures.empty:
        st.write("Schema:")
        st.dataframe(schema)

        st.write("DAX Measures:")
        st.dataframe(dax_measures[['Expression']])

        # Convert DAX expressions
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

        # Generate and download TWBX file
        twbx_path = create_twbx_file(schema, calculated_fields)
        st.success("TWBX file created successfully!")
        with open(twbx_path, 'rb') as f:
            st.download_button("Download TWBX File", f, file_name='converted_workbook.twbx')

    else:
        st.error("Failed to extract schema or measures.")

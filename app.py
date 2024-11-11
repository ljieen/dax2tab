import streamlit as st
import pandas as pd
from pbixray import PBIXRay

# Streamlit app title and description
st.title("PBIX Data Extraction Tool")
st.write("Upload a PBIX file and select an extraction option.")

# File upload widget
uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

# User option for extraction
option = st.selectbox("Select the extraction type:", ["Extract DAX Expressions", "Extract Schema", "Extract Relationships"])

# Function to extract all DAX expressions from a PBIX file
def extract_all_dax_expressions(file_path):
    try:
        model = PBIXRay(file_path)
        dax_measures = model.dax_measures

        if dax_measures.empty or 'Expression' not in dax_measures.columns:
            st.error("No DAX expressions found.")
            return None

        dax_measures['Expression'] = dax_measures['Expression'].str.replace('\n', '', regex=False)
        return dax_measures[['Expression']]
    except Exception as e:
        st.error(f"Error during DAX extraction: {e}")
        return None

# Function to extract schema from the PBIX file
def extract_schema(file_path):
    try:
        model = PBIXRay(file_path)
        schema = model.schema
        if schema.empty:
            st.error("No schema found.")
            return None
        return schema
    except Exception as e:
        st.error(f"Error during schema extraction: {e}")
        return None

# Function to extract relationships from the PBIX file
def extract_relationships(file_path):
    try:
        model = PBIXRay(file_path)
        relationships = model.relationships
        if relationships.empty:
            st.error("No relationships found.")
            return None
        return relationships
    except Exception as e:
        st.error(f"Error during relationships extraction: {e}")
        return None

# Display results based on the selected option
if uploaded_file:
    with st.spinner(f"Processing {option.lower()}..."):
        with open("temp_file.pbix", "wb") as f:
            f.write(uploaded_file.getbuffer())

        if option == "Extract DAX Expressions":
            all_dax_expressions = extract_all_dax_expressions("temp_file.pbix")
            if all_dax_expressions is not None:
                st.write("All DAX Expressions:")
                for idx, row in all_dax_expressions.iterrows():
                    st.write(f"**DAX Expression {idx + 1}:** {row['Expression']}")

        elif option == "Extract Schema":
            schema = extract_schema("temp_file.pbix")
            if schema is not None:
                st.write("Schema:")
                st.dataframe(schema)

        elif option == "Extract Relationships":
            relationships = extract_relationships("temp_file.pbix")
            if relationships is not None:
                st.write("Relationships:")
                st.dataframe(relationships)

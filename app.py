import streamlit as st
import pandas as pd
import requests
from pbixray import PBIXRay

# Streamlit app title and description
st.title("DAX to Tableau Converter Chatbot (Hugging Face Inference API)")
st.write("Upload a PBIX file to extract DAX expressions and convert them to Tableau calculated fields.")

# File upload widget
uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

# Function to extract the first 5 DAX expressions from a PBIX file
def extract_first_5_expressions(file_path):
    try:
        # Load the PBIX file and extract DAX measures
        model = PBIXRay(file_path)
        dax_measures = model.dax_measures

        # Debug: Print columns to verify structure
        st.write("DAX Measures Columns:", dax_measures.columns.tolist())

        # Check if DAX measures were extracted and if 'Expression' column exists
        if dax_measures.empty or 'Expression' not in dax_measures.columns:
            st.error("No DAX expressions were found in the uploaded PBIX file.")
            return None

        # Clean up the 'Expression' column by removing newline characters
        dax_measures['Expression'] = dax_measures['Expression'].str.replace('\n', '', regex=False)

        # Retrieve only the first 5 DAX expressions
        first_5_expressions = dax_measures[['Expression']].head(5)
        return first_5_expressions

    except Exception as e:
        st.error(f"Error during DAX extraction: {e}")
        return None

# Function to convert a single DAX expression to a Tableau calculated field using Hugging Face Inference API
def convert_dax_to_tableau(dax_expression):
    try:
        hf_token = st.secrets["HUGGINGFACE_TOKEN"]
        api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"  # Using the 7B model
        headers = {"Authorization": f"Bearer {hf_token}"}

        # Create the prompt for LLaMA
        prompt = f"Convert this DAX expression to a Tableau calculated field: {dax_expression}"
        response = requests.post(api_url, headers=headers, json={"inputs": prompt})

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            tableau_calculated_field = result[0]["generated_text"].strip()
            return tableau_calculated_field
        else:
            st.error(f"Error with Hugging Face API: {response.json()}")
            return "Conversion error"

    except Exception as e:
        st.error(f"Error during conversion: {e}")
        return "Conversion error"

# Function to display the first 5 DAX expressions and their converted Tableau fields in chatbot format
def display_converted_expressions_chatbot(first_5_expressions):
    if first_5_expressions is not None and not first_5_expressions.empty:
        st.chat_message("user").write("Can you show me the first 5 DAX expressions and their Tableau equivalents?")
        
        for idx, row in first_5_expressions.iterrows():
            dax_expression = row['Expression']
            
            # Convert each DAX expression to a Tableau calculated field
            tableau_calculated_field = convert_dax_to_tableau(dax_expression)
            
            # Display each DAX expression and its Tableau equivalent in chat format
            st.chat_message("assistant").write(f"**DAX Expression**: {dax_expression}\n**Tableau Calculated Field**: {tableau_calculated_field}")
    else:
        st.chat_message("user").write("Can you show me the first 5 DAX expressions and their Tableau equivalents?")
        st.chat_message("assistant").write("No DAX expressions were found in the uploaded PBIX file.")

# Process the uploaded file and display the chatbot interaction
if uploaded_file:
    with st.spinner("Extracting and converting DAX expressions..."):
        # Save the uploaded file temporarily
        with open("temp_file.pbix", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract the first 5 DAX expressions
        first_5_expressions = extract_first_5_expressions("temp_file.pbix")
        
        # Display the chatbot interaction with converted expressions
        display_converted_expressions_chatbot(first_5_expressions)

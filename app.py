import streamlit as st
import pandas as pd
from pbixray import PBIXRay

# Streamlit app title and description
st.title("DAX Function Extractor Chatbot")
st.write("Upload a PBIX file to extract the first 5 DAX expressions and interact in a chat format.")

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

# Function to display the first 5 DAX expressions in chatbot format
def display_expressions_chatbot(first_5_expressions):
    if first_5_expressions is not None and not first_5_expressions.empty:
        st.chat_message("user").write("Can you show me the first 5 DAX expressions?")
        
        for idx, row in first_5_expressions.iterrows():
            dax_expression = row['Expression']
            
            # Display each DAX expression in chat format
            st.chat_message("assistant").write(f"**DAX Expression**: {dax_expression}")
    else:
        st.chat_message("user").write("Can you show me the first 5 DAX expressions?")
        st.chat_message("assistant").write("No DAX expressions were found in the uploaded PBIX file.")

# Process the uploaded file and display the chatbot interaction
if uploaded_file:
    with st.spinner("Extracting DAX expressions..."):
        # Save the uploaded file temporarily
        with open("temp_file.pbix", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract the first 5 DAX expressions
        first_5_expressions = extract_first_5_expressions("temp_file.pbix")
        
        # Display the chatbot interaction
        display_expressions_chatbot(first_5_expressions)

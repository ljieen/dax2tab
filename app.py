import streamlit as st
import pandas as pd
from pbixray import PBIXRay

# Streamlit app title and description
st.title("DAX Function Extractor Chatbot")
st.write("Upload a PBIX file to extract the first DAX function and interact in a chat format.")

# File upload widget
uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

# Function to extract only the first DAX function from a PBIX file
def extract_first_dax(file_path):
    try:
        # Load the PBIX file and extract DAX measures
        model = PBIXRay(file_path)
        dax_measures = model.dax_measures

        # Check if DAX measures were extracted
        if dax_measures.empty:
            st.error("No DAX measures were found in the uploaded PBIX file.")
            return None

        # Remove newline characters from the 'Expression' column
        if 'Expression' in dax_measures.columns:
            dax_measures['Expression'] = dax_measures['Expression'].str.replace('\n', '', regex=False)
        else:
            st.error("The 'Expression' column was not found in the extracted data.")
            return None

        # Retrieve only the first DAX function for demonstration
        first_dax = dax_measures[['Measure', 'Expression']].head(1)
        return first_dax

    except Exception as e:
        st.error(f"Error during DAX extraction: {e}")
        return None

# Function to handle chatbot display of the first DAX function
def display_dax_chatbot(first_dax):
    if first_dax is not None and not first_dax.empty:
        measure_name = first_dax.iloc[0]['Measure']
        dax_expression = first_dax.iloc[0]['Expression']
        
        # Chatbot interaction: Display the DAX function as a conversation
        st.chat_message("user").write("Can you show me the first DAX function?")
        st.chat_message("assistant").write(f"**Measure**: {measure_name}\n**DAX Expression**: {dax_expression}")
    else:
        st.chat_message("user").write("Can you show me the first DAX function?")
        st.chat_message("assistant").write("No DAX functions were found in the uploaded PBIX file.")

# Process the uploaded file and display the chatbot interaction
if uploaded_file:
    with st.spinner("Extracting DAX function..."):
        # Save the uploaded file temporarily
        with open("temp_file.pbix", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract the first DAX function
        first_dax = extract_first_dax("temp_file.pbix")
        
        # Display the chatbot interaction
        display_dax_chatbot(first_dax)

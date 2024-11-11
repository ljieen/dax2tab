import streamlit as st
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from pbixray import PBIXRay
import torch

# Load LLaMA-2-70B-chat-hf Model and Tokenizer with Hugging Face Token from Streamlit Secrets
@st.cache_resource  # Cache the model to prevent reloading on every interaction
def load_llama_model():
    model_name = "meta-llama/Llama-2-70b-chat-hf"
    hf_token = st.secrets["HUGGINGFACE_TOKEN"]  # Access token securely from Streamlit secrets
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        use_auth_token=hf_token, 
        device_map="auto", 
        torch_dtype=torch.float16
    )
    llama_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, max_length=500)
    return llama_pipeline

# Initialize the LLaMA pipeline
llama_pipeline = load_llama_model()

# Streamlit app title and description
st.title("DAX to Tableau Converter Chatbot (LLaMA-2-70B)")
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

# Function to convert a single DAX expression to a Tableau calculated field using LLaMA-2
def convert_dax_to_tableau(dax_expression):
    try:
        # Create the prompt for LLaMA
        prompt = f"Convert this DAX expression to a Tableau calculated field: {dax_expression}"
        
        # Generate response using LLaMA-2 model
        response = llama_pipeline(prompt)[0]['generated_text']
        
        # Extract the generated text (Tableau calculated field)
        tableau_calculated_field = response.strip()
        return tableau_calculated_field
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

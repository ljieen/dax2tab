import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import os
import asyncio

# Load LLaMA 2 model and tokenizer
@st.cache_resource
def load_model():
    os.environ["HF_TOKEN"] = "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"
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf", use_auth_token=os.environ["HF_TOKEN"])
    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-2-7b-chat-hf",
        torch_dtype=torch.float16,
        device_map="auto",
        use_auth_token=os.environ["HF_TOKEN"]
    )
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
    return pipe

pipe = load_model()

# Title and Welcome Message
st.title("✨ DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! Let me help you convert your PowerBI reports to Tableau dashboards.")

# Sidebar for uploading file
with st.sidebar:
    st.subheader("📂 Upload Your PBIX File")
    uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

# Function to extract schema from PBIX file
def extract_schema(file_path):
    try:
        model = PBIXRay(file_path)
        schema = model.schema
        if schema.empty:
            return "No schema found."
        return schema
    except Exception as e:
        return f"Error during schema extraction: {e}"

# Function to extract all DAX expressions from PBIX file
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

# Function to convert DAX to Tableau calculated field using LLaMA 2
async def convert_dax_to_tableau(dax_expression):
    try:
        prompt = f"Convert this DAX expression to Tableau calculated field: {dax_expression}. Avoid hardcoding field names to generalize for different data sources."
        result = await asyncio.to_thread(lambda: pipe(prompt, max_length=200, num_return_sequences=1)[0]['generated_text'])
        return result
    except Exception as e:
        return f"Error during conversion: {e}"

# Block for Extracting and Converting DAX Expressions
with st.expander("🔄 2. DAX Expression Extraction and Conversion"):
    st.write("Extract the first five DAX expressions from your Power BI file and convert them into Tableau-compatible calculated fields.")

    if st.button("Extract and Convert First 5 DAX Expressions to Tableau Calculated Fields"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            dax_expressions = extract_all_dax_expressions("temp_file.pbix")

            if isinstance(dax_expressions, pd.DataFrame) and not dax_expressions.empty:
                st.write("DAX Expressions Table:")
                st.table(dax_expressions)

                # Limit to the first five expressions
                first_five_dax_expressions = dax_expressions['Expression'].head(5)

                # Convert each of the first five DAX expressions asynchronously
                tableau_calculated_fields = []
                for dax_expression in first_five_dax_expressions:
                    tableau_calculated_field = await convert_dax_to_tableau(dax_expression)
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

# Block for Q&A
with st.expander("❓ 4. Q&A"):
    st.write("Ask any questions about the conversion process, and I'll assist you.")
    question = st.text_input("Ask a question:")

    if st.button("Get Answer"):
        if question:
            response = await convert_dax_to_tableau(question)
            st.write("Answer:", response)
        else:
            st.warning("Please enter a question.")

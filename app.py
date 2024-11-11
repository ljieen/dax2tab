import streamlit as st
import pandas as pd
from pbixray import PBIXRay

# Streamlit app title and description
st.title("PBIX Data Extraction Chatbot")
st.write("Upload a PBIX file and interact with the chatbot to extract DAX expressions, schema, or relationships.")

# File upload widget
uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

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

# Chatbot interaction logic
def chatbot_interaction(option, file_path):
    if option == "Extract DAX Expressions":
        dax_expressions = extract_all_dax_expressions(file_path)
        if isinstance(dax_expressions, pd.DataFrame):
            for idx, row in dax_expressions.iterrows():
                st.chat_message("assistant").write(f"**DAX Expression {idx + 1}:** {row['Expression']}")
        else:
            st.chat_message("assistant").write(dax_expressions)

    elif option == "Extract Schema":
        schema = extract_schema(file_path)
        if isinstance(schema, pd.DataFrame):
            st.chat_message("assistant").write("Here is the schema:")
            st.dataframe(schema)
        else:
            st.chat_message("assistant").write(schema)

    elif option == "Extract Relationships":
        relationships = extract_relationships(file_path)
        if isinstance(relationships, pd.DataFrame):
            st.chat_message("assistant").write("Here are the relationships:")
            st.dataframe(relationships)
        else:
            st.chat_message("assistant").write(relationships)

# Ensure file is uploaded
if uploaded_file:
    with open("temp_file.pbix", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Show introductory message in chat
    st.chat_message("assistant").write("Hello! How can I assist you today? You can ask me to:")
    st.chat_message("assistant").write("1. Extract DAX Expressions\n2. Extract Schema\n3. Extract Relationships")

    # Option selection for chat interaction
    option = st.selectbox("Choose an option to extract:", ["Extract DAX Expressions", "Extract Schema", "Extract Relationships"])

    # Button to submit the selection
    if st.button("Submit"):
        st.chat_message("user").write(f"I would like to {option.lower()}.")
        chatbot_interaction(option, "temp_file.pbix")

import streamlit as st
import pandas as pd
from pbixray import PBIXRay

# Title and Welcome Message
st.title("DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! Let me help you convert your PowerBI reports to Tableau dashboards.")

st.subheader("1. Datasource Setup")
st.write("""
• Identify key tables/columns  
• Suggest Tableau datasource structure
""")

st.subheader("2. DAX to Tableau Conversion")
st.write("""
• Convert DAX to Tableau calculated fields  
• Explain conversions
""")

# Section 3: Platform Insights
st.subheader("3. Platform Insights")
st.write("""
    • Highlight differences between PowerBI & Tableau  
    • Offer migration tips
""")

# Q&A Section
st.subheader("4. Ask Me Anything!")
st.write("Got questions about PowerBI & Tableau? I'm here to help!")

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

# Initialize session state for Ask a Question button
if "show_question_input" not in st.session_state:
    st.session_state["show_question_input"] = False

# Display options in a 2x2 grid
col1, col2 = st.columns(2)

# Option 1: Extract DAX Expressions
with col1:
    if st.button("Extract DAX Expressions"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            dax_expressions = extract_all_dax_expressions("temp_file.pbix")
            if isinstance(dax_expressions, pd.DataFrame):
                st.write("DAX Expressions:")
                for idx, row in dax_expressions.iterrows():
                    st.write(f"**DAX Expression {idx + 1}:** {row['Expression']}")
            else:
                st.write(dax_expressions)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Option 2: Extract Schema
with col2:
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

# Option 3: Extract Relationships
with col1:
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

# Option 4: Ask a Question
with col2:
    if st.button("Ask a Question"):
        st.session_state["show_question_input"] = True  # Set flag to show the input field

# Show the question input field if the "Ask a Question" button was clicked
if st.session_state["show_question_input"]:
    question = st.text_input("Enter your question about Power BI DAX expressions:")
    if question:
        st.write("**You asked:**", question)
        st.write("Answer functionality currently requires an AI model. Add a model if needed.")

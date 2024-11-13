import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io
import openai

# Title and Welcome Message
st.title("DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! Let me help you convert your PowerBI reports to Tableau dashboards.")

# Section for entering OpenAI API Key
st.subheader("API Key Setup")
api_key_input = st.text_input("Enter your OpenAI API Key:", type="password")

# Check if API key is entered and save it to session state
if api_key_input:
    st.session_state["OPENAI_API_KEY"] = api_key_input
    openai.api_key = api_key_input
    st.success("API Key set successfully!")

# Ensure that the OpenAI API key is set before making requests
if "OPENAI_API_KEY" not in st.session_state:
    st.warning("Please enter your OpenAI API Key above to enable DAX to Tableau conversion.")

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

# Function to convert DAX to Tableau calculated field using OpenAI
def convert_dax_to_tableau(dax_expression):
    with st.spinner("Converting DAX to Tableau calculated field..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that converts DAX expressions to Tableau calculated fields."},
                {"role": "user", "content": f"Convert this DAX expression to Tableau calculated field: {dax_expression}"}
            ],
            max_tokens=150
        )
    return response.choices[0].message['content'].strip()

# Option to Extract and Convert the First DAX Expression to Tableau Calculated Field
if st.button("Extract and Convert First DAX Expression to Tableau Calculated Field"):
    if not st.session_state.get("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API Key to use the conversion feature.")
    elif uploaded_file:
        with open("temp_file.pbix", "wb") as f:
            f.write(uploaded_file.getbuffer())
        dax_expressions = extract_all_dax_expressions("temp_file.pbix")
        
        if isinstance(dax_expressions, pd.DataFrame) and not dax_expressions.empty:
            st.write("DAX Expressions Table:")
            st.table(dax_expressions)  # Display DAX expressions as a table
            
            # Get the first DAX expression
            first_dax_expression = dax_expressions['Expression'].iloc[0]
            
            # Convert the first DAX expression to Tableau equivalent
            tableau_calculated_field = convert_dax_to_tableau(first_dax_expression)
            
            # Display the converted expression
            st.write("Converted First DAX Expression to Tableau Calculated Field:")
            st.write({
                "DAX Expression": first_dax_expression,
                "Tableau Calculated Field": tableau_calculated_field
            })
        else:
            st.write(dax_expressions if isinstance(dax_expressions, str) else "No DAX expressions found.")
    else:
        st.warning("Please upload a PBIX file to proceed.")

# Initialize session state for "Ask a Question" button
if "show_question_input" not in st.session_state:
    st.session_state["show_question_input"] = False

# Option to Ask a Question to ChatGPT about DAX and Tableau
if st.button("Ask a Question"):
    st.session_state["show_question_input"] = True  # Set flag to show the input field

# Show the question input field if the "Ask a Question" button was clicked
if st.session_state["show_question_input"]:
    question = st.text_input("Enter your question about Power BI DAX expressions or Tableau:")
    if question:
        # Send the question to ChatGPT with a loading spinner
        with st.spinner("Generating answer..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant knowledgeable in Power BI DAX expressions and Tableau."},
                    {"role": "user", "content": question}
                ],
                max_tokens=200
            )
            answer = response.choices[0].message['content'].strip()
        
        # Display the response
        st.write("**Answer:**")
        st.write(answer)

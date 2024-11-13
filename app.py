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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that converts DAX expressions to Tableau calculated fields."},
            {"role": "user", "content": f"Convert this DAX expression to Tableau calculated field: {dax_expression}"}
        ],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

# Extract DAX Expressions button with conversion option
if st.button("Extract and Convert DAX Expressions"):
    if not st.session_state.get("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API Key to use the conversion feature.")
    elif uploaded_file:
        with open("temp_file.pbix", "wb") as f:
            f.write(uploaded_file.getbuffer())
        dax_expressions = extract_all_dax_expressions("temp_file.pbix")
        
        if isinstance(dax_expressions, pd.DataFrame):
            st.write("DAX Expressions Table:")
            st.table(dax_expressions)  # Display DAX expressions as a table
            
            # Convert each DAX expression to Tableau equivalent
            dax_expressions['Tableau Calculated Field'] = dax_expressions['Expression'].apply(convert_dax_to_tableau)
            
            # Display the converted expressions
            st.write("Converted DAX Expressions to Tableau Calculated Fields:")
            st.table(dax_expressions[['Expression', 'Tableau Calculated Field']])
            
            # Prepare for CSV download
            csv_buffer = io.StringIO()
            dax_expressions.to_csv(csv_buffer, index=False)
            
            # Provide download button for DAX expressions as a CSV file
            st.download_button(
                label="Download Converted DAX Expressions as CSV",
                data=csv_buffer.getvalue(),
                file_name="converted_dax_expressions.csv",
                mime="text/csv"
            )
        else:
            st.write(dax_expressions)
    else:
        st.warning("Please upload a PBIX file to proceed.")

# Initialize session state for "Ask a Question" button
if "show_question_input" not in st.session_state:
    st.session_state["show_question_input"] = False

# Additional options and existing functionalities here...
# ...

if __name__ == '__main__':
    st.write("DAX2Tab: PowerBI to Tableau Conversion Assistant is running!")

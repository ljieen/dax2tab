import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io
import openai

# Title and Welcome Message
st.title("✨ DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! Let me help you convert your PowerBI reports to Tableau dashboards.")

# Section for entering OpenAI API Key
with st.expander("🔑 API Key Setup"):
    api_key_input = st.text_input("Enter your OpenAI API Key:", type="password")

    if api_key_input:
        st.session_state["OPENAI_API_KEY"] = api_key_input
        openai.api_key = api_key_input
        st.success("API Key set successfully!")

if "OPENAI_API_KEY" not in st.session_state:
    st.warning("Please enter your OpenAI API Key above to enable DAX to Tableau conversion.")

# Layout sections in two columns
col1, col2 = st.columns(2)

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

# Function to convert DAX to Tableau calculated field using OpenAI
def convert_dax_to_tableau(dax_expression):
    with st.spinner("Converting DAX to Tableau calculated field..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that converts DAX expressions to Tableau calculated fields."},
                {"role": "user", "content": f"Convert this DAX expression to Tableau calculated field: {dax_expression}"}
            ],
            max_tokens=300
        )
    return response.choices[0].message['content'].strip()

# Sidebar for uploading file
with st.sidebar:
    st.subheader("📂 Upload Your PBIX File")
    uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

# Block for Datasource Setup
with st.expander("🔍 1. Datasource Setup"):
    st.write("• Identify key tables/columns")
    st.write("• Suggest Tableau datasource structure")

# Block for Extracting DAX Expressions and Converting
with st.expander("🔄 2. DAX to Tableau Conversion"):
    # Option 1: Extract DAX Expressions with CSV download functionality
    with col1:
        if st.button("Extract DAX Expressions"):
            if uploaded_file:
                with open("temp_file.pbix", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                dax_expressions = extract_all_dax_expressions("temp_file.pbix")
                if isinstance(dax_expressions, pd.DataFrame):
                    st.write("DAX Expressions Table:")
                    st.table(dax_expressions)

                    # Prepare DAX expressions for download as a CSV file
                    csv_buffer = io.StringIO()
                    dax_expressions.to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label="Download DAX Expressions as CSV",
                        data=csv_buffer.getvalue(),
                        file_name="dax_expressions.csv",
                        mime="text/csv"
                    )
                else:
                    st.write(dax_expressions)
            else:
                st.warning("Please upload a PBIX file to proceed.")

    # Option 2: Extract and Convert the First DAX Expression to Tableau Calculated Field
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
                
                # Follow-up Question Option
                follow_up_question = st.text_input("Ask a follow-up question about this conversion:")
                if follow_up_question:
                    with st.spinner("Generating follow-up answer..."):
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are an assistant knowledgeable in Power BI DAX expressions and Tableau."},
                                {"role": "user", "content": follow_up_question}
                            ],
                            max_tokens=500
                        )
                        follow_up_answer = response.choices[0].message['content'].strip()
                    st.write("**Follow-up Answer:**")
                    st.write(follow_up_answer)
            else:
                st.write(dax_expressions if isinstance(dax_expressions, str) else "No DAX expressions found.")
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Schema Extraction
with st.expander("🗃️ 3. Schema Extraction"):
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

# Block for Relationships Extraction
with st.expander("🔗 4. Relationships Extraction"):
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

# Block for Q&A Section with ChatGPT
with st.expander("💬 5. Ask Me Anything!"):
    question = st.text_input("Enter your question about Power BI DAX expressions or Tableau:")
    if question:
        with st.spinner("Generating answer..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant knowledgeable in Power BI DAX expressions and Tableau."},
                    {"role": "user", "content": question}
                ],
                max_tokens=500
            )
            answer = response.choices[0].message['content'].strip()
        
        st.write("**Answer:**")
        st.write(answer)

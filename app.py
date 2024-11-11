import streamlit as st
import pandas as pd
import openai
from pbixray import PBIXRay

# Streamlit app title and description
st.title("DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! I can help you convert your PowerBI reports to Tableau dashboards. Here's what I can do:")

# Section 1: Datasource Setup
st.subheader("1. Datasource Setup")
st.markdown("""
• Guide you in identifying relevant tables/columns from your PowerBI report  
• Suggest Tableau datasource structure based on your PowerBI setup
""")

# Section 2: DAX to Tableau Conversion
st.subheader("2. DAX to Tableau Conversion")
st.markdown("""
• Convert your PowerBI DAX expressions to Tableau calculated fields  
• Provide explanations for the conversions
""")

# Section 3: PowerBI vs Tableau Insights
st.subheader("3. PowerBI vs Tableau Insights")
st.markdown("""
• Highlight key differences between the platforms  
• Offers practical migration tips
""")

# Q&A Section
st.subheader("4. Ask Me Anything!")
st.write("Feel free to ask any questions about PowerBI & Tableau!")

# Input field for OpenAI API key
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

# Ensure API key is set for OpenAI
if api_key:
    openai.api_key = api_key

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

# Function to ask questions using OpenAI's GPT-3.5-turbo
def ask_openai(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}],
            max_tokens=150
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        return f"Error fetching answer: {e}"

# Chatbot interaction logic
def chatbot_interaction(option, file_path=None, question=None):
    if option == "Extract DAX Expressions" and file_path:
        dax_expressions = extract_all_dax_expressions(file_path)
        if isinstance(dax_expressions, pd.DataFrame):
            for idx, row in dax_expressions.iterrows():
                st.chat_message("assistant").write(f"**DAX Expression {idx + 1}:** {row['Expression']}")
        else:
            st.chat_message("assistant").write(dax_expressions)

    elif option == "Extract Schema" and file_path:
        schema = extract_schema(file_path)
        if isinstance(schema, pd.DataFrame):
            st.chat_message("assistant").write("Here is the schema:")
            st.dataframe(schema)
        else:
            st.chat_message("assistant").write(schema)

    elif option == "Extract Relationships" and file_path:
        relationships = extract_relationships(file_path)
        if isinstance(relationships, pd.DataFrame):
            st.chat_message("assistant").write("Here are the relationships:")
            st.dataframe(relationships)
        else:
            st.chat_message("assistant").write(relationships)

    elif option == "Ask a Question" and question:
        answer = ask_openai(question)
        st.chat_message("assistant").write(answer)

# Ensure file is uploaded
if api_key and uploaded_file:
    with open("temp_file.pbix", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Show introductory message in chat
    st.chat_message("assistant").write("Hello! You can ask me to extract DAX expressions, schema, relationships, or ask a question about Power BI DAX expressions.")

    # Option selection for chat interaction
    option = st.selectbox("Choose an action:", ["Extract DAX Expressions", "Extract Schema", "Extract Relationships", "Ask a Question"])

    # If the user selects "Ask a Question," display a text input for the question
    question = None
    if option == "Ask a Question":
        question = st.text_input("Enter your question about Power BI DAX expressions:")

    # Button to submit the selection or question
    if st.button("Submit"):
        if option == "Ask a Question" and question:
            st.chat_message("user").write(question)
            chatbot_interaction(option, question=question)
        else:
            st.chat_message("user").write(f"I would like to {option.lower()}.")
            chatbot_interaction(option, file_path="temp_file.pbix")
else:
    st.warning("Please enter your OpenAI API key to proceed.")

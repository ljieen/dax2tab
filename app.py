import streamlit as st
import requests

# Set up the Streamlit app title and description
st.title("Power BI DAX Q&A Chatbot")
st.write("Ask questions about Power BI DAX expressions, and I’ll try to help!")

# Function to call Hugging Face Inference API
def ask_huggingface(question):
    # Get the API token from Streamlit secrets
    hf_token = st.secrets["HUGGINGFACE_TOKEN"]
    # Specify the API URL for the chosen model
    api_url = "https://api-inference.huggingface.co/models/EleutherAI/gpt-j-6B"  # Example with GPT-J-6B
    headers = {"Authorization": f"Bearer {hf_token}"}

    # Create payload with the question
    payload = {"inputs": question}

    # Send POST request to Hugging Face API
    response = requests.post(api_url, headers=headers, json=payload)

    # Check for errors
    if response.status_code == 200:
        result = response.json()
        return result[0]["generated_text"].strip()
    else:
        return f"Error: {response.status_code} - {response.json()}"

# Chatbot interaction
def chatbot_interaction(question):
    answer = ask_huggingface(question)
    st.chat_message("assistant").write(answer)

# Main app logic
if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.write("## Chat Interface")
question = st.text_input("Type your question about Power BI DAX expressions:")

if st.button("Ask"):
    if question:
        st.chat_message("user").write(question)
        chatbot_interaction(question)
        st.session_state["messages"].append({"role": "user", "content": question})

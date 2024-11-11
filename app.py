import streamlit as st
import requests

# Set up the Streamlit app title and description
st.title("Power BI DAX Q&A Chatbot (Using Smaller Model)")
st.write("Ask questions about Power BI DAX expressions, and I’ll try to help!")

# Function to call Hugging Face Inference API
def ask_huggingface(question):
    hf_token = st.secrets["HUGGINGFACE_TOKEN"]
    api_url = "https://api-inference.huggingface.co/models/gpt2"  # Smaller model to fit within limits
    headers = {"Authorization": f"Bearer {hf_token}"}

    payload = {"inputs": question}
    response = requests.post(api_url, headers=headers, json=payload)

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
st.write("## Chat Interface")
question = st.text_input("Type your question about Power BI DAX expressions:")

if st.button("Ask"):
    if question:
        st.chat_message("user").write(question)
        chatbot_interaction(question)

import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import openai

# Retrieve OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Title and Welcome Message
st.title("✨ DAX2Tab: PowerBI to Tableau Conversion Assistant")
st.write("Welcome! Let me help you convert your PowerBI reports to Tableau dashboards.")

# Sidebar for uploading file
with st.sidebar:
    st.subheader("📂 Upload Your PBIX File")
    st.write("Upload your Power BI PBIX file to extract DAX expressions, schema, and relationships for conversion and analysis.")

    uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

    if uploaded_file:
        temp_path = "temp_file.pbix"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Store file path in session state
        st.session_state.pbix_file_path = temp_path
        st.success("✅ PBIX file uploaded successfully!")

# ✅ Initialize session state for section expansion
if "sections_open" not in st.session_state:
    st.session_state.sections_open = {
        "datasource": True,
        "dax_conversion": True,
        "relationships": True,
        "qna": True
    }

# ✅ Function to toggle sections
def toggle_section(key):
    st.session_state.sections_open[key] = not st.session_state.sections_open[key]

# ✅ DAX Extraction & Conversion Section
with st.expander("🔄 2. DAX Expression Extraction and Conversion", expanded=st.session_state.sections_open["dax_conversion"]):
    if st.button("Toggle DAX Section", key="toggle_dax"):
        toggle_section("dax_conversion")
    st.write("Extract and convert DAX expressions from your Power BI file into Tableau-compatible calculated fields.")

    def extract_all_dax_expressions(file_path):
        try:
            model = PBIXRay(file_path)
            dax_measures = model.dax_measures
            return dax_measures[["Expression"]] if not dax_measures.empty and "Expression" in dax_measures.columns else "No DAX expressions found."
        except Exception as e:
            return f"Error during DAX extraction: {e}"

    if "pbix_file_path" in st.session_state:
        option = st.radio("Select number of expressions to extract:", ["All", "Custom"], key="dax_option")
        num_expressions = 0 if option == "All" else st.number_input("🔢 Number of DAX expressions to extract:", min_value=1, max_value=100, value=5, key="num_dax")
        
        if st.button("🚀 Extract and Convert DAX Expressions", key="extract_convert_dax"):
            extracted_dax_df = extract_all_dax_expressions(st.session_state.pbix_file_path)
            if isinstance(extracted_dax_df, pd.DataFrame) and not extracted_dax_df.empty:
                if option == "All":
                    st.session_state.dax_expressions = extracted_dax_df["Expression"].tolist()
                else:
                    st.session_state.dax_expressions = extracted_dax_df["Expression"].tolist()[:num_expressions]
                
                # Simulate conversion to Tableau Calculated Fields
                converted_df = pd.DataFrame({
                    "DAX Expression": st.session_state.dax_expressions,
                    "Tableau Calculation": [f"Converted_{i}" for i in range(len(st.session_state.dax_expressions))]
                })
                
                st.write("### 📌 Extracted and Converted DAX Expressions")
                st.dataframe(converted_df)
                
                # Provide download link
                csv = converted_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Converted DAX Expressions",
                    data=csv,
                    file_name="converted_dax_expressions.csv",
                    mime="text/csv"
                )
            else:
                st.write(extracted_dax_df)
    else:
        st.warning("⚠️ Please upload a PBIX file first.")

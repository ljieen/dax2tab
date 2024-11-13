import streamlit as st
import pandas as pd
from pbixray import PBIXRay
import io  # For handling in-memory files

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

# Initialize session state for "Ask a Question" button
if "show_question_input" not in st.session_state:
    st.session_state["show_question_input"] = False

# Display options in a 2x2 grid
col1, col2 = st.columns(2)

# Option 1: Extract DAX Expressions with Excel download functionality
with col1:
    if st.button("Extract DAX Expressions"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            dax_expressions = extract_all_dax_expressions("temp_file.pbix")
            if isinstance(dax_expressions, pd.DataFrame):
                st.write("DAX Expressions Table:")
                st.table(dax_expressions)  # Display DAX expressions as a table

                # Prepare DAX expressions for download as an Excel file
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    dax_expressions.to_excel(writer, index=False, sheet_name='DAX Expressions')
                
                # Provide download button for DAX expressions as an Excel file
                st.download_button(
                    label="Download DAX Expressions as Excel",
                    data=excel_buffer.getvalue(),
                    file_name="dax_expressions.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write(dax_expressions)
        else:
            st.warning("Please upload a PBIX file to proceed.")

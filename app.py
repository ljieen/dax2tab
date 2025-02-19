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

# Block for Datasource Setup
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

# Expander: Datasource Setup
with st.expander("🔍 1. Datasource Setup"):
    st.write("This section helps identify key tables and columns in your Power BI data and suggests an appropriate Tableau datasource structure.")
    st.write("• Identify key tables/columns")
    st.write("• Suggest Tableau datasource structure")

    if st.button("Extract Schema"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            schema = extract_schema("temp_file.pbix")
            
            if isinstance(schema, pd.DataFrame):
                table_names = sorted(schema["TableName"].unique().tolist())
                
                st.subheader("📌 Extracted Tables and Columns")
                for table in table_names:
                    st.write(f"📂 **{table}**")
                    columns = schema[schema["TableName"] == table]["ColumnName"].tolist()
                    if columns:
                        st.write(", ".join(columns))
                    else:
                        st.write("No columns found.")
            else:
                st.write(schema)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Other sections remain the same...
# Block for Extracting and Converting DAX Expressions
with st.expander("🔄 2. DAX Expression Extraction and Conversion"):
    st.write("Extract and convert DAX expressions from your Power BI file into Tableau-compatible calculated fields.")

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
        try:
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
        except Exception as e:
            return f"Error during conversion: {e}"

    # Ensure PBIX file is uploaded
    if "pbix_file_path" not in st.session_state:
        st.warning("Please upload a PBIX file in **📂 Datasource Setup** before extracting DAX expressions.")
    else:
        # Let user choose how many DAX expressions to extract
        num_expressions = st.number_input("🔢 Number of DAX expressions to extract:", 
                                          min_value=1, max_value=100, value=5)

        extract_button = st.button("🚀 Extract DAX Expressions")

        if extract_button:
            st.session_state.dax_expressions = extract_all_dax_expressions(st.session_state.pbix_file_path)

            if isinstance(st.session_state.dax_expressions, pd.DataFrame) and not st.session_state.dax_expressions.empty:
                st.session_state.dax_expressions = st.session_state.dax_expressions['Expression'].tolist()
                st.write("### 📌 Extracted DAX Expressions")
                st.table(pd.DataFrame(st.session_state.dax_expressions, columns=["DAX Expression"]))
            else:
                st.write(st.session_state.dax_expressions)  # Show error if extraction fails

    # Ensure expressions are extracted before conversion
    if "dax_expressions" in st.session_state and st.session_state.dax_expressions:
        num_conversions = st.number_input("📊 Number of Tableau Calculated Fields to convert:", 
                                          min_value=1, 
                                          max_value=len(st.session_state.dax_expressions), 
                                          value=len(st.session_state.dax_expressions))

        convert_button = st.button("🔄 Convert DAX to Tableau")

        if convert_button:
            tableau_calculated_fields = []
            for dax_expression in st.session_state.dax_expressions[:num_conversions]:  
                tableau_calculated_field = convert_dax_to_tableau(dax_expression)
                tableau_calculated_fields.append({
                    "DAX Expression": dax_expression,
                    "Tableau Calculated Field": tableau_calculated_field
                })

            # Store conversions in session state
            st.session_state.conversions = tableau_calculated_fields
            st.session_state.chatbot_enabled = True  # Enable chatbot

            st.write("### 🎯 Converted Tableau Calculated Fields")
            for i, conversion in enumerate(tableau_calculated_fields, 1):
                st.write(f"**DAX Expression {i}:** {conversion['DAX Expression']}")
                st.write(f"**Tableau Calculated Field {i}:** {conversion['Tableau Calculated Field']}")
                st.write("---")

    # Enable chatbot **only after conversions are displayed**
    if st.session_state.get("chatbot_enabled", False):
        st.write("### 💬 Chatbot: Refine or Explain Conversions")
        
        for msg in st.session_state.get("messages", []):
            st.chat_message(msg["role"]).write(msg["content"])

        prompt = st.chat_input("Ask me to refine conversions, explain DAX, or anything else!")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You convert DAX to Tableau calculated fields conversationally."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message['content']
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(reply)

##relationship block

with st.expander("🔗 3. Relationships Extraction"):
    st.write("Extract relationships from your Power BI data model to help you maintain data integrity and relationships in Tableau.")

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

    # Function to generate SQL LEFT JOIN scripts from the relationships table for each row
    def generate_sql_scripts_from_relationships(df):
        sql_scripts = []
        current_from_table = None
        current_script = ""

        for index, row in df.iterrows():
            if row['FromTableName'] != current_from_table:
                # Start a new SQL script when the FromTableName changes
                current_from_table = row['FromTableName']
                current_script = f"FROM {current_from_table} a"
            
            # Add the LEFT JOIN for the current row
            current_row_script = f"{current_script} LEFT JOIN {row['ToTableName']} b ON a.{row['FromColumnName']} = b.{row['ToColumnName']}"
            
            sql_scripts.append(current_row_script)  # Append script for this specific row

        return sql_scripts

    if st.button("Extract Relationships"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            relationships = extract_relationships("temp_file.pbix")
            if isinstance(relationships, pd.DataFrame):
                # Filter active relationships
                active_relationships = relationships[relationships['IsActive'] == 1]
                
                # Add Suggested Joins column based on Cardinality
                active_relationships['Suggested Joins'] = active_relationships['Cardinality'].apply(
                    lambda x: 'Left join at physical layer or M:1 at logical layer' if x == 'M:1' else 'N/A'
                )
                
                # Drop all columns after 'CrossFilteringBehaviour' except 'Suggested Joins'
                if 'CrossFilteringBehaviour' in active_relationships.columns:
                    crossfilter_index = active_relationships.columns.get_loc('CrossFilteringBehaviour')
                    cols_to_keep = list(active_relationships.columns[:crossfilter_index + 1]) + ['Suggested Joins']
                    active_relationships = active_relationships.loc[:, cols_to_keep]

                # Generate SQL scripts directly from relationships table for each row
                sql_scripts = generate_sql_scripts_from_relationships(active_relationships)
                
                # Assign the SQL scripts to each row
                active_relationships['SQL Script'] = sql_scripts
                
                st.write("Active Relationships with Suggested Joins and SQL Scripts:")
                st.dataframe(active_relationships)
            else:
                st.write(relationships)
        else:
            st.warning("Please upload a PBIX file to proceed.")




# Block for Q&A Section with ChatGPT
with st.expander("💬 4. Ask Me Anything!"):
    st.write("Have any questions about Power BI, DAX expressions, or Tableau? Ask here, and I'll do my best to help you!")

    question = st.text_input("Enter your question about Power BI DAX expressions or Tableau:")
    if question:
        with st.spinner("Generating answer..."):
            try:
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
            except Exception as e:
                st.error(f"Error during question processing: {e}")

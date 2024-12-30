import os
import zipfile
import pandas as pd
import streamlit as st
from pbixray import PBIXRay
import openai
from tableauhyperapi import HyperProcess, Telemetry, Connection, CreateMode, SqlType, TableDefinition, TableName, Column, SqlExpression, Inserter

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
with st.expander("🔍 1. Datasource Setup"):
    st.write("This section helps identify key tables and columns in your Power BI data and suggests an appropriate Tableau datasource structure.")
    st.write("• Identify key tables/columns")
    st.write("• Suggest Tableau datasource structure")

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

# Block for Extracting and Converting DAX Expressions
with st.expander("🔄 2. DAX Expression Extraction and Conversion"):
    st.write("Extract the first five DAX expressions from your Power BI file and convert them into Tableau-compatible calculated fields for seamless migration.")

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

    # Extract and Convert the First 5 DAX Expressions
    if st.button("Extract and Convert First 5 DAX Expressions to Tableau Calculated Fields"):
        if not openai.api_key:
            st.error("OpenAI API key is not configured.")
        elif uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            dax_expressions = extract_all_dax_expressions("temp_file.pbix")
            
            if isinstance(dax_expressions, pd.DataFrame) and not dax_expressions.empty:
                st.write("DAX Expressions Table:")
                st.table(dax_expressions)

                # Limit to the first five expressions
                first_five_dax_expressions = dax_expressions['Expression'].head(5)

                # Convert each of the first five DAX expressions to Tableau calculated fields
                tableau_calculated_fields = []
                for i, dax_expression in enumerate(first_five_dax_expressions, 1):
                    tableau_calculated_field = convert_dax_to_tableau(dax_expression)
                    tableau_calculated_fields.append({
                        "DAX Expression": dax_expression,
                        "Tableau Calculated Field": tableau_calculated_field
                    })

                # Display converted expressions
                for i, conversion in enumerate(tableau_calculated_fields, 1):
                    st.write(f"### Conversion {i}")
                    st.write("**DAX Expression:**", conversion["DAX Expression"])
                    st.write("**Tableau Calculated Field:**", conversion["Tableau Calculated Field"])
                    st.write("---")
            else:
                st.write(dax_expressions if isinstance(dax_expressions, str) else "No DAX expressions found.")
        else:
            st.warning("Please upload a PBIX file to proceed.")

# Block for Relationships Extraction
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

# Block for converting PBIX to Tableau .twbx
with st.expander("🔁 5. Convert PBIX to Tableau (.twbx)"):
    st.write("Convert your Power BI PBIX file into a Tableau Packaged Workbook (.twbx) file.")
    
    # Function to convert PBIX data into a .csv file
    def convert_pbix_to_csv(file_path):
        try:
            model = PBIXRay(file_path)
            tables = model.tables
            if tables.empty:
                return "No tables found."
            
            csv_files = []
            for table_name, table_data in tables.items():
                csv_file = f"{table_name}.csv"
                table_data.to_csv(csv_file, index=False)
                csv_files.append(csv_file)
            
            return csv_files
        except Exception as e:
            return f"Error during CSV conversion: {e}"

    # Function to create a .hyper file from a CSV
    def create_hyper_from_csv(csv_file_path, hyper_file_path):
        try:
            with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
                with Connection(endpoint=hyper.endpoint, create_mode=CreateMode.CREATE_AND_REPLACE, database=hyper_file_path) as connection:
                    # Define schema and table
                    table_definition = TableDefinition(
                        TableName("Extract", "Extract"),
                        [Column('column_name', SqlType.text())]  # Define columns based on CSV structure
                    )
                    
                    # Create the table in the hyper file
                    connection.catalog.create_table(table_definition)
                    
                    # Insert data from CSV
                    with Inserter(connection, table_definition) as inserter:
                        df = pd.read_csv(csv_file_path)
                        for row in df.values:
                            inserter.add_row(row)
                        inserter.execute()
            return hyper_file_path
        except Exception as e:
            return f"Error during Hyper file creation: {e}"

    # Function to create a .twbx file by zipping the .twb and .hyper files
    def create_twbx(workbook_file, hyper_files):
        try:
            twbx_file = "output.twbx"
            with zipfile.ZipFile(twbx_file, 'w') as zipf:
                zipf.write(workbook_file, os.path.basename(workbook_file))
                for hyper_file in hyper_files:
                    zipf.write(hyper_file, os.path.basename(hyper_file))
            return twbx_file
        except Exception as e:
            return f"Error during TWBX creation: {e}"

    if st.button("Convert to .twbx"):
        if uploaded_file:
            with open("temp_file.pbix", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Convert PBIX data to CSV files
            csv_files = convert_pbix_to_csv("temp_file.pbix")
            if isinstance(csv_files, list):
                st.write(f"Converted CSV Files: {csv_files}")
                
                # Convert CSV files to .hyper files
                hyper_files = []
                for csv_file in csv_files:
                    hyper_file = create_hyper_from_csv(csv_file, f"{csv_file}.hyper")
                    if isinstance(hyper_file, str) and hyper_file.endswith(".hyper"):
                        hyper_files.append(hyper_file)
                
                # Create Tableau workbook (you can use a predefined .twb file or generate one dynamically)
                workbook_file = "workbook.twb"  # Assuming you have a workbook file ready
                
                # Create the .twbx file
                twbx_file = create_twbx(workbook_file, hyper_files)
                st.write(f"Successfully created Tableau .twbx file: {twbx_file}")
                
                # Provide download link for .twbx file
                with open(twbx_file, "rb") as f:
                    st.download_button(
                        label="Download Tableau Packaged Workbook (.twbx)",
                        data=f,
                        file_name=twbx_file,
                        mime="application/zip"
                    )
            else:
                st.write(csv_files)
        else:
            st.warning("Please upload a PBIX file to proceed.")

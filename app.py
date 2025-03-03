import streamlit as st
import pandas as pd
import json
import shutil
import re
from zipfile import ZipFile
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

# ✅ Datasource Setup Section
with st.expander("🔍 1. Datasource Setup", expanded=True):
    st.write("Identify key tables and columns in your Power BI data and suggest an appropriate Tableau datasource structure.")
    
    def extract_schema(file_path):
        try:
            model = PBIXRay(file_path)
            schema = model.schema
            return schema if not schema.empty else "No schema found."
        except Exception as e:
            return f"Error during schema extraction: {e}"
    
    if st.button("Extract Schema", key="extract_schema"):
        if uploaded_file:
            schema = extract_schema("temp_file.pbix")
            if isinstance(schema, pd.DataFrame):
                table_names = sorted(schema["TableName"].unique().tolist())
                st.subheader("📌 Extracted Tables and Columns")
                for table in table_names:
                    st.write(f"📂 **{table}**")
                    columns = schema[schema["TableName"] == table]["ColumnName"].tolist()
                    st.write(", ".join(columns) if columns else "No columns found.")
                
                # Provide download option
                csv = schema.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Extracted Schema",
                    data=csv,
                    file_name="extracted_schema.csv",
                    mime="text/csv"
                )
            else:
                st.write(schema)
        else:
            st.warning("Please upload a PBIX file to proceed.")

# ✅ DAX Extraction & Conversion Section
with st.expander("🔄 2. DAX Expression Extraction and Conversion", expanded=True):
    st.write("Extract DAX expressions from your Power BI file. You can choose to extract all expressions or convert selected ones into Tableau-compatible calculated fields.")

    def extract_all_dax_expressions(file_path):
        try:
            model = PBIXRay(file_path)
            dax_measures = model.dax_measures
            return dax_measures if not dax_measures.empty else "No DAX expressions found."
        except Exception as e:
            return f"Error during DAX extraction: {e}"

    def convert_dax_to_tableau(dax_expression):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You convert DAX expressions to Tableau calculated fields. Do not include the data source name or any formatting (such as currency, percentage, or date formatting) in the conversion. Formatting should be handled in Tableau separately. Ensure that the output strictly follows this rule, meaning functions like SUM([Field]) should not have currency symbols or percentage formatting in brackets."},
                    {"role": "user", "content": f"Convert this DAX expression to Tableau without including the data source name or any formatting: {dax_expression}. Provide an explanation of the Tableau calculated field conversion before giving the actual formula."}
                ],
                max_tokens=300
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            return f"Error during conversion: {e}"

    if "pbix_file_path" in st.session_state:
        extracted_dax_df = extract_all_dax_expressions(st.session_state.pbix_file_path)
        if isinstance(extracted_dax_df, pd.DataFrame) and not extracted_dax_df.empty:
            extracted_dax_df = extracted_dax_df.reset_index(drop=True)
            st.write(f"### 📌 Total DAX Expressions Found: {len(extracted_dax_df)}")
            
            # Allow filtering by DisplayFolder if available
            if "DisplayFolder" in extracted_dax_df.columns:
                display_folders = extracted_dax_df["DisplayFolder"].dropna().unique().tolist()
                display_folders.sort()
                selected_folder = st.selectbox("Filter by Display Folder", ["All"] + display_folders, key="display_folder")
                if selected_folder != "All":
                    extracted_dax_df = extracted_dax_df[extracted_dax_df["DisplayFolder"] == selected_folder]
            
            st.write("### 📄 Extracted DAX Expressions")
            st.dataframe(extracted_dax_df)
            
            csv = extracted_dax_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download DAX Expressions",
                data=csv,
                file_name="dax_expressions.csv",
                mime="text/csv"
            )
            
            selection_options = ["All"] + extracted_dax_df.index.tolist()
            selected_indices = st.multiselect("Select expressions for conversion", selection_options)
            
            if "All" in selected_indices:
                selected_indices = extracted_dax_df.index.tolist()
            
            if st.button("🚀 Convert Selected DAX Expressions to Tableau", key="convert_selected_dax"):
                selected_data = extracted_dax_df.loc[selected_indices, ["Name", "DisplayFolder", "Expression"]]
                converted_data = []
                for _, row in selected_data.iterrows():
                    conversion_result = convert_dax_to_tableau(row["Expression"])
                    explanation, formula = conversion_result.split("\n", 1) if "\n" in conversion_result else ("Explanation not provided", conversion_result)
                    converted_data.append((row["Name"], row["DisplayFolder"], row["Expression"], explanation, formula))
                
                converted_df = pd.DataFrame(converted_data, columns=["DAX Name", "Display Folder", "DAX Expression", "Tableau Explanation", "Tableau Calculation"])
                
                st.write("### 📌 Converted DAX Expressions to Tableau Calculated Fields")
                st.dataframe(converted_df)
                
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

#test 
# ✅ 2a. Original Field Mapper (Enhanced)
with st.expander("🗂️ 2a. Original Field Mapper", expanded=True):

    class ReportExtractor:
        def __init__(self, pbix_path):
            self.pbix_path = pbix_path
            self.result = []

        def extract(self):
            temp_folder = self.pbix_path.replace(".pbix", "_temp")
            try:
                shutil.rmtree(temp_folder)
            except FileNotFoundError:
                pass

            with ZipFile(self.pbix_path, 'r') as zip_ref:
                zip_ref.extractall(temp_folder)

            with open(f"{temp_folder}/Report/Layout", 'r', encoding='utf-16 le') as file:
                report_layout = json.load(file)

            fields = []
            for section in report_layout.get("sections", []):
                for visual in section.get("visualContainers", []):
                    try:
                        query_dict = json.loads(visual['config'])
                        for command in query_dict['singleVisual']['prototypeQuery']['Select']:
                            alias = command['Name'].split('.')[1]
                            table = command['Name'].split('.')[0]
                            fields.append([section['displayName'], query_dict['name'], table, alias])
                    except:
                        pass

            self.result = fields
            shutil.rmtree(temp_folder)

    def extract_renamed_columns_with_table(df, expression_col="Expression", table_col="TableName"):
        renamed_columns = []
        for _, row in df.dropna(subset=[expression_col]).iterrows():
            script = row[expression_col]
            table_name = row[table_col]

            rename_matches = re.findall(r'Table\.RenameColumns\([^,]+,\s*\{(.*?)\}\)', script)
            for match in rename_matches:
                column_pairs = re.findall(r'"([^"]+)"\s*,\s*"([^"]+)"', match)
                for original, alias in column_pairs:
                    renamed_columns.append([table_name, original, alias])

        return pd.DataFrame(renamed_columns, columns=["Table Name", "Original Column", "Alias"])

    def process_pbix(pbix_path):
        re = ReportExtractor(pbix_path)
        re.extract()
        df_metadata = pd.DataFrame(re.result, columns=['Page', 'Visual ID', 'Table', 'Alias'])

        model = PBIXRay(pbix_path)
        df_power_query = pd.DataFrame(model.power_query)

        renamed_df_with_table = extract_renamed_columns_with_table(df_power_query)

        df_merged = df_metadata.merge(
            renamed_df_with_table, how='left', left_on=['Table', 'Alias'], right_on=['Table Name', 'Alias']
        ).drop(columns=['Table Name'], errors='ignore')

        return df_merged

    if st.button("🔄 Run Field Mapping"):
        if "pbix_file_path" in st.session_state:
            field_mapping_df = process_pbix(st.session_state.pbix_file_path)
            if isinstance(field_mapping_df, pd.DataFrame) and not field_mapping_df.empty:
                st.dataframe(field_mapping_df)
                csv = field_mapping_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Mapped Fields", data=csv, file_name="mapped_fields.csv", mime="text/csv")
            else:
                st.warning("⚠️ No field mappings found.")
        else:
            st.warning("⚠️ Please upload a PBIX file first.")

##relationships


with st.expander("🔗 3. Relationships Extraction", expanded=True):
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

# ✅ Q&A Chat Section


# Initialize OpenAI model and chat history in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"  # Always use GPT-4

if "messages" not in st.session_state:
    st.session_state.messages = []

# Create the "Ask Me Anything" section inside an expander
with st.expander("💬 4. Ask Me Anything!", expanded=True):
    st.write("Have any questions about Power BI, DAX expressions, or Tableau? Ask here!")

    # Display previous messages (chat history)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 🔹 Ensure input box stays at the bottom
user_input = st.chat_input("🧑‍💬 Type your question here...")

if user_input:
    # Store user message in chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant response dynamically (streaming)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Call OpenAI's API with chat history
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=st.session_state.messages,  # Pass full chat history
            stream=True,  # Enable streaming response
        )

        # Process streaming response
        for chunk in response:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0]["delta"].get("content", "")
                full_response += delta
                message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)  # Display final response

    # Store assistant response in chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})



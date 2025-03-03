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
    uploaded_file = st.file_uploader("Choose a PBIX file", type="pbix")

    if uploaded_file:
        temp_path = "temp_file.pbix"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.pbix_file_path = temp_path
        st.success("✅ PBIX file uploaded successfully!")

# ✅ 1. Datasource Setup
with st.expander("🔍 1. Datasource Setup", expanded=True):
    def extract_schema(file_path):
        try:
            model = PBIXRay(file_path)
            return model.schema if not model.schema.empty else "No schema found."
        except Exception as e:
            return f"Error during schema extraction: {e}"
    
    if st.button("Extract Schema"):
        if uploaded_file:
            schema = extract_schema("temp_file.pbix")
            if isinstance(schema, pd.DataFrame):
                st.dataframe(schema)
                csv = schema.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Extracted Schema", data=csv, file_name="extracted_schema.csv", mime="text/csv")
        else:
            st.warning("Please upload a PBIX file.")

# ✅ 2. DAX Extraction & Conversion
with st.expander("🔄 2. DAX Expression Extraction and Conversion", expanded=True):
    def extract_all_dax_expressions(file_path):
        try:
            model = PBIXRay(file_path)
            return model.dax_measures if not model.dax_measures.empty else "No DAX expressions found."
        except Exception as e:
            return f"Error during DAX extraction: {e}"

    if "pbix_file_path" in st.session_state:
        extracted_dax_df = extract_all_dax_expressions(st.session_state.pbix_file_path)
        if isinstance(extracted_dax_df, pd.DataFrame):
            st.dataframe(extracted_dax_df)
            csv = extracted_dax_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download DAX Expressions", data=csv, file_name="dax_expressions.csv", mime="text/csv")
        else:
            st.write(extracted_dax_df)

# ✅ 3. Relationships Extraction
with st.expander("🔗 3. Relationships Extraction", expanded=True):
    def extract_relationships(file_path):
        try:
            model = PBIXRay(file_path)
            relationships = model.relationships
            return relationships if not relationships.empty else "No relationships found."
        except Exception as e:
            return f"Error during relationships extraction: {e}"

    if st.button("Extract Relationships"):
        if uploaded_file:
            relationships = extract_relationships("temp_file.pbix")
            if isinstance(relationships, pd.DataFrame):
                st.dataframe(relationships)
            else:
                st.write(relationships)
        else:
            st.warning("Please upload a PBIX file.")

# ✅ 4. Ask Me Anything! (AI Chatbot)
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.expander("💬 4. Ask Me Anything!", expanded=True):
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("🧑‍💬 Type your question here...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=st.session_state.messages,
                stream=True,
            )

            for chunk in response:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    full_response += delta
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# ✅ 5. Original Field Mapper (Enhanced)
with st.expander("🗂️ 5. Original Field Mapper", expanded=True):

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

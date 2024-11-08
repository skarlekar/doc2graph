import numpy as np
import pandas as pd
import streamlit as st
from typing import List
import os
from json_data import sample_results
from schema import Relationship, RelationshipList, RelationshipLite, RelationshipLiteList
from utils import convert_to_lite, get_dataframe, df2json, get_unique_entities
from llm import process_documents, extract_graph


def initialize_session_state():
    if 'neo4j_url' not in st.session_state:
        st.session_state.neo4j_url = ""
    if 'neo4j_username' not in st.session_state:
        st.session_state.neo4j_username = ""
    if 'neo4j_password' not in st.session_state:
        st.session_state.neo4j_password = ""
    if 'openai_api_key' not in st.session_state:
        # Initialize with environment variable if available
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = pd.DataFrame()
    if 'relationships_extracted' not in st.session_state:
        st.session_state.relationships_extracted = False
    if 'extracted_relationships' not in st.session_state:
        st.session_state.extracted_relationships = []

def display_extraction_relationships(relationships: List[RelationshipLite]):
    # Configure columns
    column_configuration = {
        "From": st.column_config.TextColumn("From", width=200),
        "Relationship": st.column_config.TextColumn("Relationship", width=200),
        "To": st.column_config.TextColumn("To", width=200)
    }

    df = get_dataframe(relationships)

    st.header("Relationships")
    st.write("Edit the entities and relationships in the table below. When you are done, click the 'Extract' button to extract the information from the documents.")
    edited_df = st.data_editor(df,
                              column_config=column_configuration,
                              use_container_width=True,
                              num_rows="dynamic",
                              hide_index=False,)
    st.session_state.edited_df = edited_df

def main():
    st.set_page_config(layout="wide", page_title="Document Graph App")
    # Initialize session state
    initialize_session_state()

        # Sidebar - Admin Section
    with st.sidebar:
        st.header("Admin")
        st.text_input("Neo4j URL", 
                     key="neo4j_url",
                     placeholder="bolt://localhost:7687")
        st.text_input("Neo4j Username", 
                     key="neo4j_username",
                     placeholder="neo4j")
        st.text_input("Neo4j Password", 
                     key="neo4j_password",
                     type="password",
                     placeholder="Enter password")
        
        # Only show OpenAI API key input if not in environment
        if not os.getenv("OPENAI_API_KEY"):
            st.text_input("OpenAI API Key",
                         key="openai_api_key",
                         type="password",
                         placeholder="Enter your OpenAI API key")

    # Main content
    tab1, tab2 = st.tabs(["Documents to Graph", "Query Graph"])
    
    with tab1:
        st.header("Upload Documents")
        uploaded_files = st.file_uploader("Choose files", 
                                        accept_multiple_files=True,
                                        type=['txt', 'pdf', 'docx'])
        
        if uploaded_files:
            api_key = os.getenv("OPENAI_API_KEY") or st.session_state.openai_api_key
            if not api_key:
                st.error("OpenAI API key not found. Please set it as an environment variable or enter it in the sidebar.")
            else:
                os.environ["OPENAI_API_KEY"] = api_key
            if not st.session_state.relationships_extracted:
                with st.spinner("Processing documents..."):
                    st.session_state.extracted_relationships = process_documents(uploaded_files)
                    st.session_state.relationships_extracted = True
            display_extraction_relationships(st.session_state.extracted_relationships)
            st.header("Relationships to Extract:")
            st.write(st.session_state.edited_df)
            allowed_relationships = df2json(st.session_state.edited_df)
            st.header("Allowed Relationships:")
            st.write(allowed_relationships)
            allowed_entities = get_unique_entities(st.session_state.edited_df)
            st.header("Allowed Entities:")
            st.write(allowed_entities)
        if st.button("Extract Graph"):
            extract_graph(uploaded_files, allowed_relationships, allowed_entities)
if __name__ == "__main__":
    main()
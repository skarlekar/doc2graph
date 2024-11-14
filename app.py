import numpy as np
import pandas as pd
import streamlit as st
from typing import List
import os
from json_data import sample_results
from schema import Relationship, RelationshipList, RelationshipLite, RelationshipLiteList
from utils import convert_to_lite, get_dataframe, df2json, get_unique_entities, insert_graph
from llm import process_documents, extract_graph


def initialize_session_state():
    if 'neo4j_url' not in st.session_state:
        st.session_state.neo4j_url = os.getenv("NEO4J_URL", "")
    if 'neo4j_username' not in st.session_state:
        st.session_state.neo4j_username = os.getenv("NEO4J_USERNAME", "")
    if 'neo4j_password' not in st.session_state:
        st.session_state.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    if 'openai_api_key' not in st.session_state:
        # Initialize with environment variable if available
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = pd.DataFrame()
    if 'relationships_extracted' not in st.session_state:
        st.session_state.relationships_extracted = False
    if 'extracted_relationships' not in st.session_state:
        st.session_state.extracted_relationships = []
    if 'extracted_graphs' not in st.session_state:
        st.session_state.extracted_graphs = []
    if 'graphDBSession' not in st.session_state:
        st.session_state.graphDBSession = None
    if 'clear_graph' not in st.session_state:
        st.session_state.clear_graph = False
    if 'reextract' not in st.session_state:
        st.session_state.reextract = False

def display_extraction_relationships(relationships: List[RelationshipLite])-> pd.DataFrame:
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
    return edited_df
    #st.session_state.edited_df = edited_df

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
        st.text_input("OpenAI API Key",
                     key="openai_api_key",
                     type="password",
                     placeholder="Enter your OpenAI API key")
        
        # Add checkbox for graph clearing
        st.session_state.clear_graph = st.checkbox(
            "Clear existing graph before insertion",
            value=False,
            help="If checked, all existing nodes and relationships will be removed before inserting new data"
        )
        st.session_state.reextract = st.checkbox(
            "Re-extract Relationships",
            value=False,
            help="If checked, the entities and relationships will be re-extracted from the documents"
        )
        

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
            if st.session_state.reextract:
                st.session_state.relationships_extracted = False
            if not st.session_state.relationships_extracted:
                with st.spinner("Processing documents..."):
                    st.session_state.extracted_relationships = process_documents(uploaded_files)
                    st.session_state.relationships_extracted = True
            st.session_state.edited_df = display_extraction_relationships(st.session_state.extracted_relationships)
            if st.button("Extract Graph"):
                with st.spinner("Extracting graph..."):
                    st.session_state.extracted_graphs = extract_graph(uploaded_files, st.session_state.edited_df)
                with st.spinner("Inserting graph..."):
                    graphDBSession = insert_graph(
                        st.session_state.extracted_graphs, 
                        st.session_state.neo4j_url, 
                        st.session_state.neo4j_username, 
                        st.session_state.neo4j_password,
                        clear_existing=st.session_state.clear_graph  # Pass the checkbox value to insert_graph
                    )
                    st.session_state.graphDBSession = graphDBSession
                    # Create a notification to the user to let them know the graph has been inserted
                    st.success("Graph inserted successfully!")
if __name__ == "__main__":
    main()
import numpy as np
import pandas as pd
import streamlit as st
from typing import List
import os
from json_data import sample_results
from schema import Relationship, RelationshipList, RelationshipLite, RelationshipLiteList
from utils import convert_to_lite, get_dataframe, df2json, get_unique_entities, insert_graph, to_sentence_case
from llm import process_documents, extract_graph
from pyvis.network import Network
import streamlit.components.v1 as components
from neo4j import GraphDatabase


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
        st.session_state.clear_graph = True
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

def create_neo4j_session():
    """Create and return a Neo4j session using environment variables"""
    try:
        driver = GraphDatabase.driver(
            st.session_state.neo4j_url,
            auth=(st.session_state.neo4j_username, st.session_state.neo4j_password)
        )
        return driver
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        return None

def visualize_graph():
    # Create a Neo4j session using the URL, username, and password from the st.session_state objects
    driver = create_neo4j_session()

    
    # Fetch graph data from Neo4j
    with st.spinner("Fetching graph data..."):
        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        # Use a session with the driver
        with driver.session(database="neo4j") as session:
            results = session.run(query)
            
            # Create a PyVis network
            net = Network(height="750px", width="100%", notebook=True)

            #Set global options for all nodes
            net.set_options("""
            {
                "nodes": {
                        "font": {
                            "size": 9,
                            "color": "red",
                            "bold": true
                        }
                },
                "edges": {
                    "font": {
                        "size": 8,
                        "color": "#000080",
                        "align": "middle"
                    }
                }
            }
            """)
            
            # Track added nodes to avoid duplicates
            added_nodes = set()
            # Process results and add to network
            for record in results:
                # Get nodes and relationship from the record
                start_node = record["n"]
                end_node = record["m"]
                relationship = record["r"]
                
                # Add start node if not already added
                if start_node.element_id not in added_nodes:
                    node_properties = dict(start_node)
                    #label = list(start_node.labels)[0]  # Get the first label
                    label = node_properties["id"]
                    title = f"{label}: {node_properties}"
                    net.add_node(start_node.element_id, 
                               label=label, 
                               title=title,
                               color="#97c2fc",
                               shape="box",
                               labelHighlightBold=True)
                               #font={'size': node_font_size, 'bold': True, 'color': 'red'})
                    added_nodes.add(start_node.element_id)
                
                # Add end node if not already added
                if end_node.element_id not in added_nodes:
                    node_properties = dict(end_node)
                    #label = list(end_node.labels)[0]  # Get the first label
                    label = node_properties["id"]
                    title = f"{label}: {node_properties}"
                    net.add_node(end_node.element_id, 
                               label=label, 
                               title=title,
                               color="#97c2fc",
                               shape="box",
                               labelHighlightBold=True)
                    added_nodes.add(end_node.element_id)
                
                # Add edge
                rel_type = type(relationship).__name__
                rel_type = to_sentence_case(rel_type)
                rel_properties = dict(relationship)
                title = f"{rel_type}: {rel_properties}"
                net.add_edge(start_node.element_id, 
                           end_node.element_id, 
                           label=rel_type,
                           title=title)
    
            # Generate the HTML file
            net.show("graph.html")
    
    # Display the network in Streamlit
    st.header("Graph")
    with open("graph.html", "r", encoding="utf-8") as f:
        html = f.read()
    components.html(html, height=800, width=1000)
    
    # Close the driver when done
    driver.close()

def main():
    st.set_page_config(layout="wide", page_title="Document Graph App")
    # Initialize session state
    initialize_session_state()

        # Sidebar - Admin Section
    with st.sidebar:
        st.header("Admin")
        neo4j_url = st.text_input("Neo4j URL", 
                                 value=st.session_state.neo4j_url,
                                 placeholder="bolt://localhost:7687")
        if neo4j_url:
            st.session_state.neo4j_url = neo4j_url
            
        neo4j_username = st.text_input("Neo4j Username", 
                                      value=st.session_state.neo4j_username,
                                      placeholder="neo4j")
        if neo4j_username:
            st.session_state.neo4j_username = neo4j_username
            
        neo4j_password = st.text_input("Neo4j Password", 
                                      type="password",
                                      value=st.session_state.neo4j_password,
                                      placeholder="Enter password")
        if neo4j_password:
            st.session_state.neo4j_password = neo4j_password
            
        st.text_input("OpenAI API Key",
                     key="openai_api_key",
                     type="password",
                     placeholder="Enter your OpenAI API key")
        
        # Add checkbox for graph clearing
        st.session_state.clear_graph = st.checkbox(
            "Clear existing graph before insertion",
            value=True,
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
                        clear_existing=st.session_state.clear_graph
                    )
                    st.session_state.graphDBSession = graphDBSession
                    st.success("Graph inserted successfully!")
                    with st.spinner("Visualizing graph..."):
                        # Add visualization after successful insertion
                        visualize_graph()
if __name__ == "__main__":
    main()
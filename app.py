"""
Doc2Graph Streamlit Application

This module provides a web-based interface for converting unstructured documents
into knowledge graphs and querying them using natural language. The application
uses Streamlit for the UI, Neo4j for graph storage, and OpenAI's GPT models for
document processing and natural language understanding.

Main Features:
- Document upload and processing (PDF, DOCX, TXT)
- Entity and relationship extraction
- Interactive graph visualization
- Natural language querying
- Neo4j database integration

Author: [Your Name]
Date: [Current Date]
"""

import numpy as np
import pandas as pd
import streamlit as st
from typing import List
import os
from schema import Relationship, RelationshipList, RelationshipLite, RelationshipLiteList
from utils import convert_to_lite, get_dataframe, df2json, get_unique_entities, insert_graph, to_sentence_case
from llm import process_documents, extract_graph
from pyvis.network import Network
import streamlit.components.v1 as components
from neo4j import GraphDatabase
from langchain.memory import ConversationBufferMemory
from prompts import QA_PROMPT, CYPHER_GENERATION_PROMPT
from utils import create_graph, create_qa_chain


def initialize_session_state():
    """
    Initialize Streamlit session state variables with default values.
    
    This function sets up all the necessary session state variables that persist
    across user interactions. It initializes database connection parameters,
    API keys, and application state variables.
    
    Session State Variables:
    - neo4j_url: Neo4j database connection URL
    - neo4j_username: Neo4j database username
    - neo4j_password: Neo4j database password
    - openai_api_key: OpenAI API key for LLM operations
    - edited_df: DataFrame containing edited relationships
    - relationships_extracted: Boolean flag indicating if relationships have been extracted
    - extracted_relationships: List of extracted relationships from documents
    - extracted_graphs: List of generated graph documents
    - graphDBSession: Neo4j database session object
    - clear_graph: Boolean flag to clear existing graph before insertion
    - reextract: Boolean flag to re-extract relationships from documents
    """
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


def display_extraction_relationships(relationships: List[RelationshipLite]) -> pd.DataFrame:
    """
    Display extracted relationships in an interactive data editor.
    
    This function creates a Streamlit data editor that allows users to view and
    modify the extracted relationships from uploaded documents. Users can edit
    entity names, relationship types, and add/remove relationships before
    generating the knowledge graph.
    
    Args:
        relationships (List[RelationshipLite]): List of extracted relationships
            from document processing
        
    Returns:
        pd.DataFrame: Edited DataFrame containing the relationships with user
            modifications
        
    Features:
        - Interactive table with editable cells
        - Dynamic row addition/removal
        - Column configuration for better UX
        - Real-time data validation
    """
    # Configure columns for better user experience
    column_configuration = {
        "From": st.column_config.TextColumn("From", width=200),
        "Relationship": st.column_config.TextColumn("Relationship", width=200),
        "To": st.column_config.TextColumn("To", width=200)
    }

    # Convert relationships to DataFrame for display
    df = get_dataframe(relationships)

    # Display header and instructions
    st.header("Relationships")
    st.write("Edit the entities and relationships in the table below. When you are done, click the 'Extract' button to extract the information from the documents.")
    
    # Create interactive data editor
    edited_df = st.data_editor(df,
                              column_config=column_configuration,
                              use_container_width=True,
                              num_rows="dynamic",
                              hide_index=False,)
    return edited_df


def create_neo4j_session():
    """
    Create and return a Neo4j database session.
    
    This function establishes a connection to the Neo4j database using the
    credentials stored in the session state. It handles connection errors
    gracefully and provides user feedback.
    
    Returns:
        GraphDatabase.driver: Neo4j driver object if connection successful,
            None otherwise
        
    Error Handling:
        - Displays error message if connection fails
        - Returns None to allow graceful error handling in calling functions
    """
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
    """
    Create and display an interactive graph visualization.
    
    This function fetches graph data from Neo4j, creates a PyVis network
    visualization, and displays it in the Streamlit interface. The visualization
    shows nodes (entities) and edges (relationships) with customizable styling.
    
    Process:
        1. Connect to Neo4j database
        2. Query all nodes and relationships
        3. Create PyVis network with custom styling
        4. Add nodes and edges to the network
        5. Generate HTML visualization
        6. Display in Streamlit interface
        
    Features:
        - Interactive node and edge highlighting
        - Custom node colors and shapes
        - Hover tooltips with node/edge details
        - Responsive layout
        - Automatic duplicate node handling
    """
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

            # Set global options for all nodes
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
                    # label = list(start_node.labels)[0]  # Get the first label
                    label = node_properties["id"]
                    title = f"{label}: {node_properties}"
                    net.add_node(start_node.element_id, 
                               label=label, 
                               title=title,
                               color="#97c2fc",
                               shape="box",
                               labelHighlightBold=True)
                    added_nodes.add(start_node.element_id)
                
                # Add end node if not already added
                if end_node.element_id not in added_nodes:
                    node_properties = dict(end_node)
                    # label = list(end_node.labels)[0]  # Get the first label
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
    """
    Main application function that sets up the Streamlit interface.
    
    This function initializes the application, creates the user interface,
    and handles all user interactions. It manages two main tabs:
    1. Documents to Graph: For document upload and graph generation
    2. Query Graph: For natural language querying of the knowledge graph
    
    Interface Components:
        - Sidebar: Configuration and settings
        - Tab 1: Document processing and graph generation
        - Tab 2: Natural language querying
        
    User Workflow:
        1. Configure database and API settings in sidebar
        2. Upload documents in Tab 1
        3. Review and edit extracted relationships
        4. Generate knowledge graph
        5. Switch to Tab 2 for querying
        6. Ask natural language questions
        7. View results and generated Cypher queries
    """
    # Configure Streamlit page settings
    st.set_page_config(layout="wide", page_title="Document Graph App")
    
    # Initialize session state
    initialize_session_state()

    # Sidebar - Admin Section
    with st.sidebar:
        st.header("Admin")
        
        # Neo4j Connection Settings
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
            
        # OpenAI API Key Input (only show if not in environment)
        if not os.getenv("OPENAI_API_KEY"):
            st.text_input("OpenAI API Key",
                         key="openai_api_key",
                         type="password",
                         placeholder="Enter your OpenAI API key")
        
        # Graph Management Options
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

    # Main content area with tabs
    tab1, tab2 = st.tabs(["Documents to Graph", "Query Graph"])
    
    # Tab 1: Document Processing and Graph Generation
    with tab1:
        st.header("Upload Documents")
        
        # File upload widget
        uploaded_files = st.file_uploader("Choose files", 
                                        accept_multiple_files=True,
                                        type=['txt', 'pdf', 'docx'])
        
        if uploaded_files:
            # Validate OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY") or st.session_state.openai_api_key
            if not api_key:
                st.error("OpenAI API key not found. Please set it as an environment variable or enter it in the sidebar.")
            else:
                os.environ["OPENAI_API_KEY"] = api_key
                
            # Handle re-extraction flag
            if st.session_state.reextract:
                st.session_state.relationships_extracted = False
                
            # Process documents if relationships haven't been extracted
            if not st.session_state.relationships_extracted:
                with st.spinner("Processing documents..."):
                    st.session_state.extracted_relationships = process_documents(uploaded_files)
                    st.session_state.relationships_extracted = True
                    
            # Display and edit relationships
            st.session_state.edited_df = display_extraction_relationships(st.session_state.extracted_relationships)
            
            # Graph extraction button
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
    
    # Tab 2: Natural Language Querying
    with tab2:
        st.title("Neo4j Graph Query Interface")
        
        # Schema refresh functionality
        if st.button("Refresh Schema"):
            st.session_state.graph = create_graph()
            if st.session_state.graph:
                st.session_state.graph.refresh_schema()
                st.success("Schema refreshed successfully!")
                
        # Create graph connection if not exists
        if 'graph' not in st.session_state:
            st.session_state.graph = create_graph()
        
        if st.session_state.graph:
            # Display the graph schema
            st.header("Graph Schema")
            st.code(st.session_state.graph.schema, language="text")
            
            # Conversation management
            if st.sidebar.button("Clear Conversation"):
                if 'memory' in st.session_state:
                    st.session_state.memory.clear()
                    st.success("Conversation history cleared!")
            
            # Query interface
            st.header("Query Interface")
            user_query = st.text_area("Enter your question:", height=100)
            
            if st.button("Submit Query"):
                if not user_query:
                    st.warning("Please enter a question.")
                else:
                    try:
                        # Create QA chain for processing queries
                        chain = create_qa_chain(st.session_state.graph)
                        
                        # Execute query and get response
                        with st.spinner("Processing query..."):
                            result = chain({"query": user_query})
                            
                            # Display intermediate steps (Cypher queries)
                            st.subheader("Generated Cypher Query:")
                            if isinstance(result["intermediate_steps"], list):
                                for step in result["intermediate_steps"]:
                                    if "query" in step:
                                        st.code(step["query"], language="cypher")
                                    if "context" in step:
                                        st.subheader("Query Context:")
                                        st.json(step["context"])
                            
                            # Display final answer
                            st.subheader("Answer:")
                            st.write(result["result"])
                            
                            # Display conversation history
                            if 'memory' in st.session_state:
                                st.subheader("Conversation History:")
                                for message in st.session_state.memory.chat_memory.messages:
                                    if hasattr(message, 'content'):
                                        st.text(f"{message.type}: {message.content}")
                            
                    except Exception as e:
                        st.error(f"Error processing query: {str(e)}")
                        st.exception(e)
        else:
            st.error("Unable to connect to Neo4j database. Please check your connection settings.")


if __name__ == "__main__":
    main()
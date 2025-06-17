import streamlit as st
import os
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components

def initialize_session_state():
    """Initialize session state variables with environment variables"""
    if 'neo4j_url' not in st.session_state:
        st.session_state.neo4j_url = os.getenv("NEO4J_URL", "")
    if 'neo4j_username' not in st.session_state:
        st.session_state.neo4j_username = os.getenv("NEO4J_USERNAME", "")
    if 'neo4j_password' not in st.session_state:
        st.session_state.neo4j_password = os.getenv("NEO4J_PASSWORD", "")

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
    """Fetch data from Neo4j and create a visualization"""
    driver = create_neo4j_session()
    if not driver:
        return
    
    try:
        # Create a PyVis network
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
        
        # Fetch all nodes and relationships
        with driver.session(database="neo4j") as session:
            # Query to get all nodes and relationships
            query = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            """
            
            results = session.run(query)
            
            # Track added nodes to avoid duplicates
            added_nodes = set()
            
            # Process results and add to network
            for record in results:
                # Get nodes and relationship from the record
                start_node = record["n"]
                end_node = record["m"]
                relationship = record["r"]
                
                # Add start node if not already added
                if start_node.id not in added_nodes:
                    node_properties = dict(start_node)
                    label = list(start_node.labels)[0]  # Get the first label
                    title = f"{label}: {node_properties}"
                    net.add_node(start_node.id, 
                               label=label, 
                               title=title,
                               color="#97c2fc")
                    added_nodes.add(start_node.id)
                
                # Add end node if not already added
                if end_node.id not in added_nodes:
                    node_properties = dict(end_node)
                    label = list(end_node.labels)[0]  # Get the first label
                    title = f"{label}: {node_properties}"
                    net.add_node(end_node.id, 
                               label=label, 
                               title=title,
                               color="#97c2fc")
                    added_nodes.add(end_node.id)
                
                # Add edge
                rel_type = type(relationship).__name__
                rel_properties = dict(relationship)
                title = f"{rel_type}: {rel_properties}"
                net.add_edge(start_node.id, 
                           end_node.id, 
                           label=rel_type,
                           title=title)
        
        # Generate the HTML file
        net.save_graph("graph.html")
        
        # Display the graph
        with open("graph.html", "r", encoding="utf-8") as f:
            html = f.read()
        components.html(html, height=800)
        
    except Exception as e:
        st.error(f"Error visualizing graph: {str(e)}")
    finally:
        driver.close()

def main():
    st.set_page_config(page_title="Neo4j Graph Visualizer", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    st.title("Neo4j Graph Visualizer")
    
    # Display connection info
    st.sidebar.header("Connection Information")
    st.sidebar.text(f"URL: {st.session_state.neo4j_url}")
    st.sidebar.text(f"Username: {st.session_state.neo4j_username}")
    
    # Add refresh button
    if st.sidebar.button("Refresh Graph"):
        visualize_graph()
    else:
        # Show graph on initial load
        visualize_graph()

if __name__ == "__main__":
    main()

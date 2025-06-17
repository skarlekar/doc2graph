import pandas as pd
import streamlit as st
from typing import List, Dict

from schema import Relationship, RelationshipList, RelationshipLite, RelationshipLiteList
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase
from config import LLM_CONFIG
from langchain.memory import ConversationBufferMemory
from prompts import CYPHER_GENERATION_PROMPT, QA_PROMPT

def convert_to_lite(relationships: List[Relationship]) -> List[RelationshipLite]:
    unique_results = []
    seen = set()
    for r in relationships:
        key = (r.head_type, r.relation, r.tail_type)
        if key not in seen:
            seen.add(key)
            # Create a RelationshipLite object with check=False
            lite_relationship = RelationshipLite(
                head_type=r.head_type,
                relation=r.relation,
                tail_type=r.tail_type,
                check=False
            )
            unique_results.append(lite_relationship)
    return unique_results

def get_dataframe(results: List[RelationshipLite]) -> pd.DataFrame:

    data = [{
        'From': item.head_type,
        'Relationship': item.relation,
        'To': item.tail_type
    } for item in results]

    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

def df2json(df):
    """
    Convert a DataFrame with 'From', 'Relationship', 'To' columns to a list of tuples
    
    Args:
        df (pandas.DataFrame): DataFrame containing the relationships
        
    Returns:
        list: List of tuples in format [(from_node, relationship, to_node), ...]
    """
    if df.empty:
        return []
        
    # Convert DataFrame rows to list of tuples
    relationships = [
        (str(row['From']), str(row['Relationship']), str(row['To'])) 
        for _, row in df.iterrows()
    ]
    
    return relationships

def get_unique_entities(df):
    """
    Extract unique entities from the 'From' and 'To' columns of a DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame containing 'From' and 'To' columns
        
    Returns:
        list: List of unique entities sorted alphabetically
    """
    if df.empty:
        return []
        
    # Combine 'From' and 'To' columns and get unique values
    unique_entities = pd.concat([df['From'], df['To']]).unique().tolist()
    
    # Sort alphabetically for consistent output
    return sorted(unique_entities)

def clean_graph(graphDBSession: Neo4jGraph):
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    graphDBSession.query(query)

def create_graphDBSession(url: str, username: str, password: str, refresh_schema: bool = False) -> Neo4jGraph:    
    return Neo4jGraph(url=url, username=username, password=password, refresh_schema=refresh_schema)

# Function to insert the graph into the neo4j database. This function takes an array of graphs and inserts them into the database.
def insert_graph(graphs: list[Dict], uri: str, user: str, password: str, clear_existing: bool = False) -> Neo4jGraph:
    # Initialize the Neo4j driver by using the credentials passed as parameters to this function
    graphDBSession = create_graphDBSession(uri, user, password)
    if clear_existing:
        clean_graph(graphDBSession)

    for graph in graphs:
        print(f"Inserting graph: {graph}")
        graphDBSession.add_graph_documents(graph, baseEntityLabel=True)

    return graphDBSession


def to_sentence_case(text: str) -> str:
    """Convert a string from any case to sentence case.
    Example: 'HELLO_WORLD' -> 'Hello world'
    """
    # First convert to lowercase
    text = text.lower()
    # Replace underscores and hyphens with spaces
    text = text.replace('_', ' ').replace('-', ' ')
    # Capitalize first letter
    return text.capitalize()

def create_graph():
    """Create and return a Neo4j graph connection"""
    try:
        graph = Neo4jGraph(
            url=st.session_state.neo4j_url,
            username=st.session_state.neo4j_username,
            password=st.session_state.neo4j_password,
            enhanced_schema=True
        )
        return graph
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        return None

def create_qa_chain(graph):
    """Create and return a GraphCypherQAChain with separate LLMs for Cypher and QA"""
    # LLM for generating Cypher queries
    cypher_llm = ChatOpenAI(
        model=LLM_CONFIG["model"],
        temperature=LLM_CONFIG["temperature"],
        api_key=st.session_state.openai_api_key
    )
    
    # LLM for generating natural language answers
    qa_llm = ChatOpenAI(
        model=LLM_CONFIG["model"],
        temperature=LLM_CONFIG["temperature"],
        api_key=st.session_state.openai_api_key
    )
    
    # Initialize memory in session state if not exists
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="query",
            output_key="result"
        )
    
    # Create the chain with both LLMs, custom prompt, and memory
    chain = GraphCypherQAChain.from_llm(
        cypher_llm=cypher_llm,
        qa_llm=qa_llm,
        graph=graph,
        verbose=True,
        return_intermediate_steps=True,
        validate_cypher=True,
        allow_dangerous_requests=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        qa_prompt=QA_PROMPT,
        memory=st.session_state.memory  # Add memory to the chain
    )
    
    return chain
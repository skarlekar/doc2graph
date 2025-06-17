import streamlit as st
import os
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase
from config import LLM_CONFIG
from langchain_core.prompts.prompt import PromptTemplate
from langchain.memory import ConversationBufferMemory
QA_PROMPT_TEMPLATE = """
You are an AI assistant that helps generate human-readable answers based on database query results.
The latest prompt contains the information, and you need to generate a human readable response based on the given information.
Make it sound like the information is coming from an AI assistant, but don't add any information that isn't in the results.

If the result is empty or null, state that clearly.
If the result contains data, include ALL the information from the results in your response.
Do not add any additional information that is not explicitly provided in the query results.
Do not apologize or explain how you generated the answer.

Question: {question}
Database Results: {context}

Please provide a natural language response using only the information given above.
"""

QA_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=QA_PROMPT_TEMPLATE
)

# Define the Cypher generation template
CYPHER_GENERATION_TEMPLATE = """
Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
If the question is about a person, use the Person node.
If the question is about an organization, use the Organization node.
If the question is about a customer, use both Person and Organization nodes.
When asked for customers, you need to consider both Person and Organization nodes.
When constructing the Cypher query, all sub queries in an UNION must have the same return column names
The MET_WITH, CO_WORKED_WITH, COORDINATED_WITH relationships are bidirectional relationships and should be used with <-[:MET_WITH]->, <-[:CO_WORKED_WITH]->, <-[:COORDINATED_WITH]-> respectively.

Examples: Here are a few examples of generated Cypher statements for particular questions:
# What is the revenue of NVIDIA?
```
MATCH (m:Financial_Metric {{id:"Revenue"}})-[r:INCREASED]->(v:Financial_Value)
RETURN m.id, v.id
```
# Who founded Genesis Bank? or Who was the founder of Genesis Bank? or Who is the founder of Genesis Bank?
```
MATCH (p:Person)-[r:FOUNDED]->(o:Organization {{id: "Genesis Bank"}})
RETURN p.id
```
# Who was hired by Alex Thompson? or Whom did Alex Thompson hire?
```
MATCH (p:Person{{id:"Alex Thompson"}})<-[r:HIRED|HIRED_BY]->(h:Person) RETURN h.id
```
# Who are all the customers of Genesis Bank?
```
MATCH (c:Person)-[r:RELIES_ON|UTILIZES|USES]->(:Organization {{id: "Genesis Bank"}})
RETURN c.id
UNION
MATCH (c:Organization)-[r:RELIES_ON|UTILIZES|USES]->(:Organization {{id: "Genesis Bank"}})
RETURN c.id
```
# Whom did Alex Thompson meet with?
```
MATCH (p:Person {{id: "Alex Thompson"}})<-[r:MET_WITH]->(m:Person)
RETURN m.id
```
Notice that the query above uses bidirectional relationship MET_WITH and uses <-[:MET_WITH]-> instead of <-[:MET_WITH]- or ->[:MET_WITH]-> since a meeting is a bidirectional relationship.

# What is the nature of the relationship between Alex Thompson and Daniel Reed? 
```
MATCH (p1:Person {{id: "Alex Thompson"}})<-[r:MET_WITH|COORDINATED_WITH|HIRED|HIRED_BY]->(p2:Person {{id: "Daniel Reed"}})
RETURN type(r) AS relationship
```
#How are Alex Thompson and Daniel Reed related?
```
MATCH (p1:Person {{id: "Alex Thompson"}})<-[r:MET_WITH|COORDINATED_WITH|HIRED|HIRED_BY|REPORTS_TO]->(p2:Person {{id: "Daniel Reed"}})
RETURN type(r) AS relationship
UNION
MATCH (p1:Person {{id: "Alex Thompson"}})<-[r:MET_WITH|COORDINATED_WITH|HIRED|HIRED_BY|REPORTS_TO]-(p2:Person {{id: "Daniel Reed"}})
RETURN type(r) AS relationship
```

# Does Alex Thompson know Daniel Reed?
```
cypher
MATCH (p1:Person {{id: "Alex Thompson"}})<-[r:MET_WITH|COORDINATED_WITH|HIRED|HIRED_BY|REPORTS_TO]-(p2:Person {{id: "Daniel Reed"}})
RETURN type(r) AS relationship
```
The result of the above query is either MET_WITH or COORDINATED_WITH. Therefore, the answer is "Yes, Alex Thompson knows Daniel Reed because they met with each other".

Schema:
{schema}

The question is:
{question}

"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

def initialize_session_state():
    """Initialize session state variables with environment variables"""
    if 'neo4j_url' not in st.session_state:
        st.session_state.neo4j_url = os.getenv("NEO4J_URL", "")
    if 'neo4j_username' not in st.session_state:
        st.session_state.neo4j_username = os.getenv("NEO4J_USERNAME", "")
    if 'neo4j_password' not in st.session_state:
        st.session_state.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

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

def main():
    st.set_page_config(page_title="Neo4j Graph Query Interface", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    st.title("Neo4j Graph Query Interface")
    
    # Display connection info in sidebar
    with st.sidebar:
        st.header("Connection Information")
        st.text(f"URL: {st.session_state.neo4j_url}")
        st.text(f"Username: {st.session_state.neo4j_username}")
        
        # Add refresh schema button
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
        
        # Add a clear conversation button
        if st.sidebar.button("Clear Conversation"):
            if 'memory' in st.session_state:
                st.session_state.memory.clear()
                st.success("Conversation history cleared!")
        
        # Create query interface
        st.header("Query Interface")
        user_query = st.text_area("Enter your question:", height=100)
        
        if st.button("Submit Query"):
            if not user_query:
                st.warning("Please enter a question.")
            else:
                try:
                    # Create QA chain
                    chain = create_qa_chain(st.session_state.graph)
                    
                    # Execute query and get response
                    with st.spinner("Processing query..."):
                        result = chain({"query": user_query})
                        
                        # Display intermediate steps
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
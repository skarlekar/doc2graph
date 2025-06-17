from langchain.prompts import PromptTemplate

ENTITY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["content"],
    template='''You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph. Your task is to identify the entities and relations specified in the user prompt from a given text and produce the output in JSON format. This output should be a list of JSON objects, with each object containing the following keys:

- "head": The text of the extracted entity, which must match one of the types specified in the user prompt.
- "head_type": The type of the extracted head entity, selected from the specified list of types.
- "relation": The type of relation between the "head" and the "tail," chosen from the list of allowed relations.
- "tail": The text of the entity representing the tail of the relation.
- "tail_type": The type of the tail entity, also selected from the provided list of types.

Text content: {content}

Return only the JSON array with no additional text or explanations.'''
) 

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
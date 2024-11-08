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
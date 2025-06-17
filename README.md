# Doc2Graph

Transform unstructured documents into interactive knowledge graphs and query them using natural language.

## Description

Doc2Graph is a powerful tool that converts unstructured documents (PDFs, Word documents, and text files) into a knowledge graph stored in Neo4j. It uses advanced NLP techniques to extract entities and relationships from documents, allowing users to query the information using natural language. The application provides an intuitive web interface built with Streamlit for document processing, graph visualization, and natural language querying.

## Features

- **Document Processing**
  - Support for multiple document formats:
    - PDF (.pdf)
    - Microsoft Word (.docx)
    - Text files (.txt)
  - Automatic entity and relationship extraction
  - Interactive relationship editing interface

- **Graph Generation**
  - Automatic conversion of documents to knowledge graphs
  - Neo4j graph database integration
  - Interactive graph visualization
  - Customizable entity and relationship types

- **Natural Language Querying**
  - Intuitive query interface
  - Support for complex relationship queries
  - Conversation history tracking
  - Real-time query results

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/doc2graph.git
cd doc2graph
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export NEO4J_URL="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
export OPENAI_API_KEY="your_openai_api_key"
```

4. Run the application:
```bash
streamlit run app.py
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Neo4j Database (version 5.17.0 or higher)
- OpenAI API key

### Dependencies
Key dependencies include:
- streamlit>=1.39.0
- neo4j>=5.17.0
- langchain>=0.3.7
- langchain-openai>=0.0.2
- python-docx>=0.8.11
- PyPDF2>=3.0.1
- pandas>=2.0.0
- pyvis>=0.3.2

### Virtual Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Running the Application
1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Access the web interface at `http://localhost:8501`

### Basic Workflow
1. **Upload Documents**
   - Click "Upload Documents" in the "Documents to Graph" tab
   - Select one or more PDF, DOCX, or TXT files

2. **View and Edit Relationships**
   - Review extracted relationships in the interactive table
   - Edit entity names and relationship types as needed
   - Click "Extract Graph" to generate the knowledge graph

3. **Query the Graph**
   - Switch to the "Query Graph" tab
   - Enter natural language questions
   - View results and generated Cypher queries

### Example Queries
- "What is the revenue of NVIDIA?"
- "Who founded Genesis Bank?"
- "Who was hired by Alex Thompson?"
- "Who are all the customers of Genesis Bank?"
- "Whom did Alex Thompson meet with?"
- "What is the nature of the relationship between Alex Thompson and Daniel Reed?"

## Architecture

### Technology Stack
- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: Neo4j
- **NLP/ML**: 
  - LangChain
  - OpenAI GPT-4
  - LLMGraphTransformer

### Data Flow
1. Document Upload → Text Extraction
2. Text → Entity/Relationship Extraction (LLM)
3. Relationships → Graph Generation
4. Graph → Neo4j Storage
5. Natural Language Query → Cypher Query → Results

## Configuration

### Environment Variables
- `NEO4J_URL`: Neo4j database connection URL
- `NEO4J_USERNAME`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `OPENAI_API_KEY`: OpenAI API key

### Configuration Files
- `config.py`: LLM configuration settings
- `prompts.py`: System prompts for LLM interactions

## UI Documentation

### Main Interface
- **Sidebar**
  - Neo4j Connection Settings
  - OpenAI API Key Input
  - Graph Management Options

### Documents to Graph Tab
- File Upload Widget
- Relationship Editor Table
- Extract Graph Button
- Graph Visualization

### Query Graph Tab
- Query Input Text Area
- Submit Query Button
- Results Display
- Conversation History
- Schema Display

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Setup
1. Clone the repository
2. Install development dependencies
3. Set up pre-commit hooks
4. Run tests

### Coding Standards
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions
- Include unit tests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

### Reporting Issues
- Use the GitHub issue tracker
- Include detailed reproduction steps
- Provide relevant logs and screenshots

### FAQ
1. **Q: Why is my graph not showing up?**
   A: Check your Neo4j connection settings and ensure the database is running.

2. **Q: How do I handle large documents?**
   A: The system processes documents in chunks. For very large documents, consider splitting them into smaller files.

3. **Q: Can I customize the entity types?**
   A: Yes, you can edit the relationships in the interactive table before graph generation.

## Contact

For support or questions, please open an issue in the GitHub repository.

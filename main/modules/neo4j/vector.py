from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.graphs import Neo4jGraph

from langchain.graphs.graph_document import (
    Node as BaseNode,
    Relationship as BaseRelationship,
    GraphDocument,
)
from langchain.schema import Document
from typing import List, Dict, Any, Optional
from langchain.pydantic_v1 import Field, BaseModel
import os
import concurrent.futures
from langchain.chains.openai_functions import (
    create_openai_fn_chain,
    create_structured_output_chain,
)
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List
from tqdm import tqdm

class Property(BaseModel):
  """A single property consisting of key and value"""
  key: str = Field(..., description="key")
  value: str = Field(..., description="value")

class Node(BaseNode):
    properties: Optional[List[Property]] = Field(
        None, description="List of node properties")

class Relationship(BaseRelationship):
    properties: Optional[List[Property]] = Field(
        None, description="List of relationship properties"
    )

class KnowledgeGraph(BaseModel):
    """Generate a knowledge graph with entities and relationships."""
    nodes: List[Node] = Field(
        ..., description="List of nodes in the knowledge graph")
    rels: List[Relationship] = Field(
        ..., description="List of relationships in the knowledge graph"
    )

def format_property_key(s: str) -> str:
    words = s.split()
    if not words:
        return s
    first_word = words[0].lower()
    capitalized_words = [word.capitalize() for word in words[1:]]
    return "".join([first_word] + capitalized_words)

def props_to_dict(props) -> dict:
    """Convert properties to a dictionary."""
    properties = {}
    if not props:
      return properties
    for p in props:
        properties[format_property_key(p.key)] = p.value
    return properties

def map_to_base_node(node: Node) -> BaseNode:
    """Map the KnowledgeGraph Node to the base Node."""
    properties = props_to_dict(node.properties) if node.properties else {}
    # Add name property for better Cypher statement generation
    properties["name"] = node.id.title()
    return BaseNode(
        id=node.id.title(), type=node.type.capitalize(), properties=properties
    )


def map_to_base_relationship(rel: Relationship) -> BaseRelationship:
    """Map the KnowledgeGraph Relationship to the base Relationship."""
    source = map_to_base_node(rel.source)
    target = map_to_base_node(rel.target)
    properties = props_to_dict(rel.properties) if rel.properties else {}
    return BaseRelationship(
        source=source, target=target, type=rel.type, properties=properties
    )


def get_extraction_chain(
    credentials: dict,
    allowed_nodes: Optional[List[str]] = None,
    allowed_rels: Optional[List[str]] = None
    ):
    
    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
            # Knowledge Graph Instructions for GPT-4
            ## 1. Overview
            You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph from the Stack Overflow Python preprocessed dataset.
            - **Nodes** represent entities and concepts related to questions, answers, users, tags, titles, and technical concepts.
            - The aim is to achieve simplicity and clarity in the knowledge graph, making it accessible for a vast audience.

            ## 2. Labeling Nodes
            - **Consistency**: Ensure you use basic or elementary types for node labels.
              - For example, when you identify an entity representing a question, always label it as **"question"**. Avoid using more specific terms like "pythonQuestion" or "listComprehensionQuestion".
            - **Node IDs**: Use meaningful identifiers from the text, such as question IDs, answer IDs, or user names.
            - **Allowed Node Labels:** "question", "answer", "user", "tag", "title", "technicalConcept", "function", "method", "class", "module"
            - **Allowed Relationship Types:** "ASKS", "ANSWERS", "HAS_ANSWER", "TAGGED_WITH", "HAS_TITLE", "USES", "CONTAINS", "CALLS", "IMPORTS"

            ## 3. Handling Numerical Data
            - Numerical data, such as view counts or answer scores, should be incorporated as attributes or properties of the respective nodes.
            - **No Separate Nodes for Numbers**: Do not create separate nodes for numerical values. Always attach them as attributes or properties of nodes.
            - **Property Format**: Properties must be in a key-value format.
            - **Quotation Marks**: Never use escaped single or double quotes within property values.
            - **Naming Convention**: Use camelCase for property keys.

            ## 4. Coreference Resolution
            - **Maintain Entity Consistency**: When extracting entities, it's vital to ensure consistency.
              If an entity is mentioned multiple times in the text but is referred to by different names or pronouns, always use the most complete identifier for that entity throughout the knowledge graph.

            ## 5. Entity and Relation Extraction
            - **Entities to Extract:**
              - Questions
              - Answers
              - Users
              - Tags
              - Titles
              - Technical Concepts
              - Functions
              - Methods
              - Classes
              - Modules
            - **Relationships to Extract:**
              - ASKS: Relationship between a user and a question.
              - ANSWERS: Relationship between a user and an answer.
              - HAS_ANSWER: Relationship between a question and its answers.
              - TAGGED_WITH: Relationship between a question and its tags.
              - HAS_TITLE: Relationship between a question and its title.
              - USES: Relationship between functions, classes, modules and the modules they utilize.
              - CONTAINS: Relationship between answers and technical concepts or examples mentioned within them.
              - CALLS: Relationship between functions, methods, or classes when one calls or uses another.
              - IMPORTS: Relationship between modules indicating a dependency or usage of another module.

            ## 6. Extracting Function and Method Details
            - **Function and Method Attributes**: Extract attributes such as `name`, `parameters`, `returnType`, and `module` for functions and methods.

            ## 7. Predict Query Example
            The extracted knowledge graph should be able to answer the following query:
            MATCH (f:Function)-[:USES]->(:Module name: 'PyDev')-[:IMPORTS]->(m:Module)
            WHERE f.name = 'PyDev'
            RETURN f, m;
            """),
        ("human", "Use the given format to extract information from the following input: {input}"),
        ("human", "Tip: Make sure to answer in the correct format"),
    ]
)
    try:
        # OpenAI credentials
        openai_api_secret_key = credentials["openai_api_secret_key"]
        openai_api_base = credentials["openai_api_base"]
        
        llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0,
            openai_api_key=openai_api_secret_key,
            openai_api_base=openai_api_base
        )

        return create_structured_output_chain(KnowledgeGraph, llm, prompt, verbose=False)
    except Exception as e:
        print(f"Validation error in get_extraction_chain: {e}")
        # 处理错误，返回一个默认值或执行其他逻辑
        return None

def extract_and_store_graph(
    document: Document,
    credentials: dict,
    nodes:Optional[List[str]] = None,
    rels:Optional[List[str]]=None) -> None:
    try:
        # Extract graph data using OpenAI functions
        extract_chain = get_extraction_chain(credentials, nodes, rels)
        data = extract_chain.run(document.page_content)
        # Construct a graph document
        graph_document = GraphDocument(
        nodes = [map_to_base_node(node) for node in data.nodes],
        relationships = [map_to_base_relationship(rel) for rel in data.rels],
        source = document
        )
        return graph_document

    except Exception as e:
        print(f"An unexpected error occurred in extract_and_store_graph: {e}")
        # 处理其他类型的错误
        return None

def store_data_in_neo4j(documents, credentials):
    """
    Store data with kg in Neo4j.
    """
    # Neo4j Aura credentials
    url = credentials["url"]
    username = credentials["username"]
    password = credentials["password"]


    graph = Neo4jGraph(
        url=url,
        username=username,
        password=password
    )

    for document in tqdm(documents, total=len(documents)):
        graph_document = extract_and_store_graph(document, credentials, nodes=None, rels=None)
        graph.add_graph_documents([graph_document])
import json
import sagemaker
import boto3
import re
import openai
from modules.environment.environment_utilities import (
    load_environment_variables,
    verify_environment_variables,
)
from modules.datasources.data import load_data, process_data
from modules.langchain.langchain import initialize_qa_workflow, execute_qa_workflow
from modules.neo4j.credentials import neo4j_credentials
from modules.neo4j.vector import (
    store_data_in_neo4j
)
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.graphs import Neo4jGraph
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri


# def load_data_and_store_openai_embeddings_in_neo4j_vector():
#     try:
#         print(
#             f"\nLoad data from Wikipedia and store OpenAI embeddings in a Neo4j Vector\n\t"
#         )

#         raw_docs = load_wikipedia_data()
#         processed_docs = process_wikipedia_data(raw_docs)
#         store_data_in_neo4j(processed_docs, neo4j_credentials)

#     except Exception as e:
#         print(f"\n\tAn unexpected error occurred: {e}")


# def query_against_an_existing_neo4j_vector(index_name, query):
#     try:
#         print(f"\nQuery against an existing Neo4j Vector\n\tQuery: {query}\n")

#         # Instantiate Neo4j vector from an existing vector
#         neo4j_vector = initialize_neo4j_vector(neo4j_credentials, index_name)

#         # Perform the similarity search and display results
#         results = perform_similarity_search(neo4j_vector, query)

#         # Close the Neo4j connection
#         neo4j_vector._driver.close()

#         # Do something with the results
#         print(results[0].page_content)

#     except Exception as e:
#         print(f"\n\tAn unexpected error occurred: {e}")


# def question_answer_workflow_with_langchain(index_name, query):
#     try:
#         print(f"\nQuestion/Answer workflow with LangChain\n\tQuery: {query}\n")

#         neo4j_vector = initialize_neo4j_vector(neo4j_credentials, index_name)

#         # Initialize and execute the QA workflow
#         qa_workflow = initialize_qa_workflow(
#             neo4j_vector, neo4j_credentials["openai_api_secret_key"]
#         )

#         qa_results = execute_qa_workflow(
#             neo4j_vector, qa_workflow, query, neo4j_credentials["openai_api_secret_key"]
#         )
#         print(qa_results["answer"])

#         # Close the Neo4j connection
#         neo4j_vector._driver.close()

#     except Exception as e:
#         print(f"\n\tAn unexpected error occurred: {e}")

def create_graph():
    try:
        print(
            f"\nstore Knowledge graph in Neo4j\n\t"
        )

        raw_docs = load_data()
        processed_docs = process_data(raw_docs)
        store_data_in_neo4j(processed_docs, neo4j_credentials)

    except Exception as e:
        print(f"\n\tAn unexpected error occurred: {e}")


def graph_cycher_QA_chain(query):
    try:
        graph = Neo4jGraph(
            url=neo4j_credentials["url"], 
            username=neo4j_credentials["username"], 
            password=neo4j_credentials["password"]
        )
    
        # print(graph.schema)
    
        chain = GraphCypherQAChain.from_llm(
            ChatOpenAI(temperature=0, openai_api_key=neo4j_credentials["openai_api_secret_key"]), 
            graph=graph, 
            verbose=True
        )

        graph_result = chain.run(query)
        print(graph_result)

    except Exception as e:
        print(f"\n\tAn unexpected error occurred: {e}")


def answer_generation(query, graph_result): 
    
    final_prompt = f"""You are a helpful question-answering agent. Your task is to analyze 
    and synthesize information from one sources: relevant data from a graph database (structured information). 
    Given the user's query: {query}, provide a meaningful and efficient answer based 
    on the insights derived from the following data:

    Structured information: {graph_result}.
    """
    
    openai.api_key = neo4j_credentials["openai_api_secret_key"]
    openai.api_base = neo4j_credentials["openai_api_base"]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful question-answering agent."},
            {"role": "user", "content": final_prompt}
        ]
    )

    response_content = response['choices'][0]['message']['content']
    html_response = format_response_to_html(response_content)
    print(html_response)

def format_response_to_html(response):
    # 使用正则表达式提取每个步骤并进行格式化
    steps = re.split(r'\n\d+\.\s\*\*', response)
    html_response = "<html><body>"
    html_response += f"<p>{steps[0]}</p>"  # 引言部分

    for i, step in enumerate(steps[1:], start=1):
        html_response += f"<h2>Step {i}</h2><p>{step.strip()}</p>"

    html_response += "</body></html>"
    return html_response



# Main program
try:
    # Load environment variables using the utility
    env_vars = load_environment_variables()
    VECTOR_INDEX_NAME = "vector"

    # Verify the environment variables
    if not verify_environment_variables(env_vars):
        raise ValueError("Some environment variables are missing!")

    create_graph()

except Exception as e:
    print(f"An unexpected error occurred: {e}")

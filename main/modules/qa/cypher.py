from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.graphs import Neo4jGraph

graph = Neo4jGraph(
    url="neo4j+ssc://f385138b.databases.neo4j.io", 
    username="neo4j", 
    password="lRHZ8E4DD53PbDnqSMs4N920STJx6TXivCGPheLWnck"
)

print(graph.schema)

chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0), graph=graph, verbose=True
)

graph_result = chain.run('How to overcome "datetime.datetime not JSON serializable" in python?')
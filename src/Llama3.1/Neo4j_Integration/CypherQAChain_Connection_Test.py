
from langchain_community.llms import Ollama
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

# Neo4j connection
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="Password1"
)

# LLM Model
model = Ollama(model="llama3.1")

# Cypher Chain
cypher_chain = GraphCypherQAChain.from_llm(llm=model, graph=graph, allow_dangerous_requests=True)

print("CypherQAChain successfully initialized!")

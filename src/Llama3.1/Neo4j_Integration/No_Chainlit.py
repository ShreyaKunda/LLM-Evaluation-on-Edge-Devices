from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
 
question = input("Enter your question: ")
 
# Initialize the Neo4j graph --------------------------------------------------------------------------
try:
    graph = Neo4jGraph(
        url="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    print("Connected to Neo4j successfully")
except Exception as e:
    print(f"Error connecting to Neo4j: {e}")
 
#  Initialize the GraphCypherQAChain --------------------------------------------------------------------------
model = OllamaLLM(model="llama3.1")  # Load the LLM model
graph_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI that can answer questions using a Neo4j knowledge graph. You generate Cypher queries and return accurate answers. You're a very knowledgeable Cypher query generator.Your task is to provide users with a correct and a precise cypher query along with the response. If anything else is asked, tell the user that it is beyond your ability. Do not provide any personal information. Please read the user question carefully and use the words to understand what they want from the graph. If you dont know the answer, just reply with I don't know and dont provide any Cyphe Query for the reply."),
            ("human", "{query}")
        ])
 
graph_qa_chain = GraphCypherQAChain.from_llm(
    llm=model, graph=graph, prompt=graph_prompt, return_intermediate_steps=True, allow_dangerous_requests=True
)
 
result = graph_qa_chain.invoke({"query":question})
 
print(result)
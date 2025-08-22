from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
import chainlit as cl
import os

# ------------------- Authentication -------------------
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin", metadata={"role": "admin", "provider": "credentials"})
    else:
        return None

# ------------------- Neo4j Graph Setup -------------------
try:
    graph = Neo4jGraph(
        url="bolt://localhost:7687",  
        password="Password1"  
    )
    print("Connected to Neo4j successfully!")
except Exception as e:
    print(f"Failed to connect to Neo4j: {e}")

# ------------------- Helper Functions for Query History -------------------
def update_query_history(user_id: str, query_text: str):
    cypher = """
    MERGE (u:User {id: $user_id})
    MERGE (q:Query {text: $query_text})
    MERGE (u)-[r:ASKED]->(q)
    ON CREATE SET r.count = 1
    ON MATCH SET r.count = r.count + 1
    """
    params = {"user_id": user_id, "query_text": query_text}
    graph.query(cypher, params)

def get_top_queries(user_id: str, limit: int = 3):
    cypher = """
    MATCH (u:User {id: $user_id})-[r:ASKED]->(q:Query)
    RETURN q.text as query, r.count as count
    ORDER BY r.count DESC
    LIMIT $limit
    """
    params = {"user_id": user_id, "limit": limit}
    result = graph.query(cypher, params)
    top_queries = [row["query"] for row in result]
    return top_queries

# ------------------- Chat Initialization -------------------
@cl.on_chat_start
async def on_chat_start():
    """Initialize chatbot session, setup prompts, and handle user selections."""
    
    model = Ollama(model="llama3.1")  # Load the LLM model
    memory = ConversationBufferMemory(memory_key="chat_history")  # Chat memory
    cl.user_session.set("memory", memory)  # Store memory in session

    res = await cl.AskActionMessage(
        content="Hello! How can I assist you today?",
        actions=[
            cl.Action(name="Graph QA", payload={"value": "Graph QA"}, label="Graph Question Answering"),
            cl.Action(name="Insights from text files", payload={"value": "Insights from text files"}, label="Insights from text files"),
        ],
    ).send()
    
    # ------------------- Graph QA -------------------
    if res and res.get("payload", {}).get("value") == "Graph QA":
        await cl.Message(content="You're now in Graph QA mode.").send()
        
        graph_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI that can answer questions using a Neo4j knowledge graph. You generate Cypher queries and return accurate answers. You're a very knowledgeable Cypher query generator. Your task is to provide users with a correct and precise Cypher query along with the response. If anything else is asked, tell the user that it is beyond your ability."),
            ("human", "{query}")
        ])
        
        graph_qa_chain = GraphCypherQAChain.from_llm(
            llm=model, graph=graph, prompt=graph_prompt, return_intermediate_steps=True, allow_dangerous_requests=True
        )
        cl.user_session.set("runnable", graph_qa_chain)

# ------------------- Message Handling -------------------
@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages, update persistent query history, provide answers, and show recommendations."""
    
    chain = cl.user_session.get("runnable")
    memory = cl.user_session.get("memory")  # Retrieve chat memory

    # Safely retrieve user ID (using message.author; adjust as needed)
    if hasattr(message.author, "id"):
        user_id = message.author.id
    else:
        user_id = message.author  # if author is a string
    
    if not user_id:
        user_id = "default_user"
    
    query_text = message.content

    # Update persistent query history in Neo4j.
    update_query_history(user_id, query_text)

    if not chain:
        await cl.Message(content="Graph QA is not initialized. Please restart the chat.").send()
        return
    
    try:
        thinking_msg = await cl.Message(content="Processing the request...").send()
        
        response = await chain.ainvoke({"query": query_text})
        
        generated_query = response.get("intermediate_steps", ["No query generated"])[0]
        final_answer = response.get("result", "I don't know the answer.")
        
        memory.save_context({"query": query_text}, {"response": final_answer})
        
        await thinking_msg.delete()
        
        await cl.Message(
            content=f"**Generated Cypher Query:**\n```\n{generated_query}\n```\n\n**Answer:**\n{final_answer}"
        ).send()
        
        # Fetch persistent top queries for the user from Neo4j.
        top_queries = get_top_queries(user_id, limit=3)
        
        if top_queries:
            actions = [cl.Action(name="recommend", payload={"query": q}, label=q) for q in top_queries]
            actions.append(cl.Action(name="continue_chat", payload={"action": "continue"}, label="Continue to chat"))
            
            res_action = await cl.AskActionMessage(
                content="Select one of your frequent queries to ask, or choose 'Continue to chat' to proceed:",
                actions=actions
            ).send()
            
            if res_action:
                payload = res_action.get("payload", {})
                if payload.get("action") == "continue":
                    await cl.Message(content="Continuing the chat... please ask your question!").send()
                elif payload.get("query"):
                    recommended_query = payload.get("query")
                    rec_thinking = await cl.Message(content="Processing recommended query...").send()
                    rec_response = await chain.ainvoke({"query": recommended_query})
                    rec_generated_query = rec_response.get("intermediate_steps", ["No query generated"])[0]
                    rec_final_answer = rec_response.get("result", "I don't know the answer.")
                    memory.save_context({"query": recommended_query}, {"response": rec_final_answer})
                    await rec_thinking.delete()
                    await cl.Message(
                        content=f"**Generated Cypher Query:**\n```\n{rec_generated_query}\n```\n\n**Answer:**\n{rec_final_answer}"
                    ).send()
    
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()
        print(f"Error processing query: {str(e)}")



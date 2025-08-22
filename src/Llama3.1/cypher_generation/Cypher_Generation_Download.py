from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.schema import StrOutputParser
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl
import os

# ------------------- Authentication -------------------

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Authentication for admin users
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None

# ------------------- Chat Initialization -------------------

@cl.on_chat_start
async def on_chat_start():
    """ Initialize chatbot session, setup prompts, and handle user selections. """
    
    model = Ollama(model="llama3.1")  # Load the LLM model
    memory = ConversationBufferMemory(memory_key="chat_history")  # Chat memory

    res = await cl.AskActionMessage(
        content="Hello! How can I assist you today?",
        actions=[
            cl.Action(name="Cypher Query Generation", 
                      payload={"value": "Cypher Query Generation"}, 
                      label="Cypher Query Generation"),
            cl.Action(name="Cypher Query Explanation", 
                      payload={"value": "Cypher Query Explanation"}, 
                      label="Cypher Query Explanation"),
        ],
    ).send()

    # ------------------- Cypher Query Generation -------------------
    if res and res.get("payload").get("value") == "Cypher Query Generation":
        await cl.Message(
            content="Sure, let's get started! What Cypher queries would you like me to generate?"
        ).send()
        
        # Define the Cypher query generation prompt
        cypher_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You're a very knowledgeable Cypher query generator. You're name is CypherBot. When you are asked questions like what is your name or who are you, say that your name is CypherBot. Your task is the to give users with proper and correct Cypher queries based on their requests. If you are asked anything other than generating Cypher Queries, please do not give any information. In such conditions, just say that you cannot answer that question and you can only answer Cypher Query Generation questions. While generating a response, make sure to answer to the point and do not give any additional sentences or text to the user. If a user asks you to give an explanation or a description of a cypher query, please respond by asking them to choose the other mode in the start which is Cypher Query Explanation and just provide the query.]"),
                ("human", "{question}")
            ]
        )

        # Create the Cypher query generation chain with memory
        cypher_chain = LLMChain(llm=model, prompt=cypher_prompt, memory=memory)

        # Store the chain in user session
        cl.user_session.set("runnable", cypher_chain)

    # ------------------- Text File Insights -------------------
    else:
        files = None
        while files is None:
            files = await cl.AskFileMessage(
                content="Great! Please put forward your Cypher Query and I will break it down and explain it to you!", 
                accept=["text/plain"]
            ).send()

        text_file = files[0]
        with open(text_file.path, "r", encoding="utf-8") as f:
            text = f.read()

        await cl.Message(
            content=f"`{text_file.name}` uploaded."
        ).send()

        # Define the text insights prompt
        insights_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You're a very knowledgeable Cypher query explanator. Your task is to provide users with a detailed explanation of the cypher query provided by the user.  If anything else except explanation and giving clear points is asked, tell the user that it is beyond your ability. Do not provide any personal information. "),
                ("human", "{question}")
            ])
        

        # Create the text insights chain with memory
        insights_chain = LLMChain(llm=model, prompt=insights_prompt, memory=memory)

        # Store the chain in user session
        cl.user_session.set("runnable", insights_chain)

# ------------------- Message Handling -------------------

@cl.on_message
async def on_message(message: cl.Message):
    """ Handle user messages, generate Cypher queries, and provide download options. """
    
    chain = cl.user_session.get("runnable")  # Retrieve the appropriate LLM chain
    response = await chain.arun({"question": message.content})  # Generate response
    
    # Display the generated Cypher query
    await cl.Message(content=f"Here is your generated Cypher Query:\n\n```cypher\n{response}\n```").send()
    
    

    # Save the query to a text file for downloading
    file_path = "/home/administrator/workspace/Shreya/LLM_Evaluation/Codes/Text_Files/Generated_Queries/generated_query.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response)

    # Provide a download button for the user
    await cl.Message(
        content="",
        file=cl.File(path=file_path, name="cypher_query.txt")
    ).send()

    # Clean up the file after sending
    os.remove(file_path)

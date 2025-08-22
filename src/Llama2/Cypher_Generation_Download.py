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

    
    model = Ollama(model="llama2")  # Load the LLM model
    memory = ConversationBufferMemory(memory_key="chat_history")  # Chat memory

    res = await cl.AskActionMessage(
        content="Hello! How can I assist you today?",
        actions=[
            cl.Action(name="Cypher Query Generation", 
                      payload={"value": "Cypher Query Generation"}, 
                      label="Query Generation"),
            cl.Action(name="Insights from text files", 
                      payload={"value": "Insights from text files"}, 
                      label="Insights from text files"),
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
                ("system", "You're a very knowledgeable Cypher query generator. You're name is CypherBot. Your task is the to give users with proper and correct Cypher queries based on their requests. If you are asked anything other than generating Cypher Queries, please do not give any information. In such conditions, just say that you cannot answer that question and you can only answer Cypher Query and related questions. While generating a response, make sure to answer to the point and do not give any additional sentences or text to the user."),
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
                content="Great! Please upload your text file, and I will summarize it for you!", 
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
                ("system", "You're a very knowledgeable data insights generator. Your task is to provide users with summaries and bullet points from text files. You should be precise and clear when you give them the answer. highlight and bold important things. If the user has not given you any data to summarize and produce precise bullet points from, ask the user to provide you with it. If anything else except summarizing and giving clear points is asked, tell the user that it is beyond your ability. Do not provide any personal information."),
                ("human", "{question}")
            ])
        

        # Create the text insights chain with memory
        insights_chain = LLMChain(llm=model, prompt=insights_prompt, memory=memory)

        # Store the chain in user session
        cl.user_session.set("runnable", insights_chain)

# ------------------- Message Handling -------------------

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
    # Save the query to a text file for downloading
    file_path = "/home/administrator/workspace/Shreya/LLM_Evaluation/Codes/Text_Files/Generated_Queries/generated_query.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response)

    # Provide a download button for the user
    await cl.Message(
        content="Click below to download your query:",
        file=cl.File(path=file_path, name="cypher_query.txt")
    ).send()

    # Clean up the file after sending
    os.remove(file_path)

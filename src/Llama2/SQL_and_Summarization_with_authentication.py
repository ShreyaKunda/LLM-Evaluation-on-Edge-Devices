from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "Password1"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None

@cl.on_chat_start
async def on_chat_start():

    model = Ollama(model="llama2")
    res = await cl.AskActionMessage(
        content="Hello! How have you been? What would you like me to help you with today?",
        actions=[
            cl.Action(name=" Cypher Query Generation", payload={"value": "Cypher Query Generation"}, label="Query Generation"),
            cl.Action(name="Insights from data", payload={"value": "Insights from the data"}, label="Insights from the data"),
        ],
    ).send()

    if res and res.get("payload").get("value") == "Cypher Query Generation":
        await cl.Message(
            content="Sure, let's get started! What cypher queries would you like me to generate today?",
        ).send()
        prompt_generation = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You're a very knowledgeable Cypher query generator. You're name is CypherBot. Your task is the to give users with proper and correct Cypher queries based on their requests. If you are asked anything other than generating Cypher Queries, please do not give any information. In such conditions, just say that you cannot answer that question and you can only answer Cypher Query and related questions.",
                ),
                ("human", "{question}"),
            ]
        )
        runnable = prompt_generation | model | StrOutputParser()
        cl.user_session.set("runnable", runnable)
    else:
        await cl.Message(
            content="Great! What can I do for you?",
        ).send()
        prompt_data = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You're a very knowledgeable data insights generator. Your task is to provide users with summaries and bullet points from text. You should be precise and clear when you give them the answer. highlight and bold important things. If the user has not given you any data to summarize and produce precise bullet points from, ask the user to provide you with it. If anything else except summarizing and giving clear points is asked, tell the user that it is beyond your ability. Do not provide any personal information.",
                ),
                ("human", "{question}"),
            ]
        )
        runnable = prompt_data | model | StrOutputParser()
        cl.user_session.set("runnable", runnable)


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



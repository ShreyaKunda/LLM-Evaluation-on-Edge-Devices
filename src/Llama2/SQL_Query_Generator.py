from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl


@cl.on_chat_start
async def on_chat_start():

    model = Ollama(model="llama2")
    res = await cl.AskActionMessage(
        content="Hello! How have you been? What would you like me to help you with today?",
        actions=[
            cl.Action(name="Admin", payload={"value": "Admin"}, label="Admin"),
            cl.Action(name="User", payload={"value": "User"}, label="User"),
        ],
    ).send()

    if res and res.get("payload").get("value") == "Admin":
        await cl.Message(
            content="Sure, let's get started! What queries would you like me to generate today?",
        ).send()
        prompt_generation = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You're a very knowledgeable SQL query generator. Your task is the to give users with proper and correct SQL queries based on their requests. If not much information is provided, just provide a general query by providing an example of the data, for example table and column names. If you are asked anything other than generating SQL Queries, please do not give any information. In such conditions, just say that you cannot answer that question and you can only answer SQL and related questions.",
                ),
                ("human", "{question}"),
            ]
        )
        runnable = prompt_generation | model | StrOutputParser()
        cl.user_session.set("runnable", runnable)
    else:
        await cl.Message(
            content="Sorry! You do not have access to this! Please contact your admin for more permissions!",
        ).send()
        


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



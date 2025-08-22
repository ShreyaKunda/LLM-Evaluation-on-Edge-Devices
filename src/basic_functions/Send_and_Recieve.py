
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from chainlit import message
import chainlit as cl


predefined_answers={"what is my location":"You are in India", "who are you?":"I am a chatbot","how are you?":"I am good, How about you?", "Hello":"Hello, how can I assist you today?"}


def get_predefined(user_input):

    return predefined_answers.get(user_input, "i dont understand what you are saying")
@cl.on_chat_start
async def main():
    await cl.Message(content="Hi Welcome").send()
@cl.on_message
async def handle_message(message_text:cl.Message):
    response=get_predefined(message_text)
    await cl.Message(content=f"Recieved: {message_text.content}", ).send()

import chainlit as cl

# Predefined answers dictionary
predefined_answers = {
    "what is my location": "You are in India",
    "who are you?": "I am a chatbot",
    "how are you?": "I am good, How about you?",
    "Hello": "Hello, how can I assist you today?"
}

# Function to check predefined answers
def get_predefined(user_input):
    return predefined_answers.get(user_input.lower(), "I don't know what you're asking.")

@cl.on_chat_start
async def main():
    # Ask the user to enter a question
    await cl.Message(content="Hello! Please ask your question.").send()

@cl.on_message
async def handle_message(message_text: cl.Message):
    # Get the user question
    user_question = message_text.content
    # Get predefined response based on the question
    response = get_predefined(user_question)
    # Send the response back to the user
    await cl.Message(content=response).send()

@cl.on_window_message
async def window_message(message: str):
    if message.startswith("Client: "):
        await cl.Message(content=f"Window message received: {message}").send()

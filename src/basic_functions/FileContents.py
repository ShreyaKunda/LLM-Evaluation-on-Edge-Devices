import chainlit as cl


@cl.on_chat_start
async def start():
    elements = [
        cl.File(
            name="Hello.txt",
            path="/home/administrator/workspace/Shreya/Llama2/Generated_Queries",
            display="inline",
        ),
    ]

    await cl.Message(
        content="This message has a file element", elements=elements
    ).send()


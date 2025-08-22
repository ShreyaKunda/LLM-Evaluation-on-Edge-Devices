import chainlit as cl
from chainlit.input_widget import Slider


@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            Slider(
                id="Temperature",
                label="OpenAI - Temperature",
                initial=1,
                min=0,
                max=2,
                step=0.1,
            ),
        ]
    ).send()
    value = settings["Temperature"]



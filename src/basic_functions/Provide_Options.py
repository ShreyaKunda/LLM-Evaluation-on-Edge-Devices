import chainlit as cl


@cl.on_chat_start
async def main():
    res = await cl.AskActionMessage(
        content="Select your role",
        actions=[
            cl.Action(name="Admin", payload={"value": "Admin"}, label="Admin"),
            cl.Action(name="User", payload={"value": "User"}, label="User"),
        ],
    ).send()

    if res and res.get("payload").get("value") == "Admin":
        await cl.Message(
            content="Continue!",
        ).send()

import chainlit as cl

@cl.action_callback("action_button")
async def on_action(action):
    await cl.Message(content=f"Executed {action.name}").send()
    # Optionally remove the action button from the chatbot user interface
    await action.remove()

@cl.on_chat_start
async def start():
    # Sending an action button within a chatbot message
    actions = [
        cl.Action(name="action_button", payload={"value": "example_value"}, label="Click me!")
    ]

    await cl.Message(content="Interact with this action button:", actions=actions).send()


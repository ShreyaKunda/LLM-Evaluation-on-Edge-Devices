import os
import chainlit as cl
@cl.on_message
async def on_message(message: cl.Message):
    chain = cl.user_session.get("runnable")
    cypher_query = await chain.arun({"question": message.content})

    # Send the generated Cypher query to the user
    await cl.Message(content=f"Here is your generated Cypher Query:\n\n```cypher\n{cypher_query}\n```").send()

    # Save the query to a text file
    file_path = "generated_cypher_query.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(cypher_query)

    # Provide a download button for the user
    await cl.Message(
        content="Click below to download your query:",
        file=cl.File(path=file_path, name="cypher_query.txt")
    ).send()

    # Clean up the file after sending
    os.remove(file_path)

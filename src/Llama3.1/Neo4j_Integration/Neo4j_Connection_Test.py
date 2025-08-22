from langchain_neo4j import Neo4jGraph

# Connect to Neo4j
graph = Neo4jGraph(
    url="bolt://localhost:7687",  # Replace with correct URL
    username="neo4j",
    password="Password1"  # Replace with your actual password
)

# Check if it connects successfully
print("Graph schema:", graph.get_schema)

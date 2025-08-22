from neo4j import GraphDatabase

# Connect to Neo4j
uri = "bolt://localhost:7687"
username = "neo4j"
password = "Password1"  # Change to your actual password

driver = GraphDatabase.driver(uri, auth=(username, password))

# Query function
def get_students_in_course(course_name):
    query = """
    MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {name: $course_name})
    RETURN s.name
    """
    with driver.session() as session:
        result = session.run(query, course_name=course_name)
        return [record["s.name"] for record in result]

# Example: Get students in Mathematics
students = get_students_in_course("Mathematics")
print("Students in Mathematics:", students)

# Close connection
driver.close()

from python_graphql_client import GraphqlClient
import asyncio
import json
# Instantiate the client with an endpoint.
client = GraphqlClient(endpoint="http://52.59.243.101:4000/graphql")

# Create the query string and variables required for the request.
query = """
    mutation {
        generateAccessToken(data: {
            email: "shipping32@shoclef.com",
            password: "Shoclef123"
        })
    }
"""

# Asynchronous request

data = asyncio.run(client.execute_async(query=query))
print(json.loads(data))

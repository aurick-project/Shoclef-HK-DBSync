from python_graphql_client import GraphqlClient
import asyncio

# Instantiate the client with an endpoint.
client = GraphqlClient(endpoint="http://52.59.243.101:4000/graphql")

# Create the query string and variables required for the request.
query = """
    query GetProduct{
        product(id:"fff00a1e-f7b1-40ac-ac62-1fe2924bd149"){
            title
            description
        }
    }
"""

# # Synchronous request
# data = client.execute(query=query, variables=variables)
# print(data)  # => {'data': {'country': {'code': 'CA', 'name': 'Canada'}}}
#

# Asynchronous request

data = asyncio.run(client.execute_async(query=query))
print(data)  # => {'data': {'country': {'code': 'CA', 'name': 'Canada'}}}

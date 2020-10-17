from python_graphql_client import GraphqlClient
import asyncio

# Instantiate the client with an endpoint.
client = GraphqlClient(endpoint="https://countries.trevorblades.com")

# Create the query string and variables required for the request.
query = """
    query countryQuery($countryCode: String) {
        country(code:$countryCode) {
            code
            name
        }
    }
"""
variables = {"countryCode": "CA"}

# # Synchronous request
# data = client.execute(query=query, variables=variables)
# print(data)  # => {'data': {'country': {'code': 'CA', 'name': 'Canada'}}}
#

# Asynchronous request

data = asyncio.run(client.execute_async(query=query, variables=variables))
print(data)  # => {'data': {'country': {'code': 'CA', 'name': 'Canada'}}}

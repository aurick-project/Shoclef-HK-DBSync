from python_graphql_client import GraphqlClient
from hk.settings import hk_graphql
import asyncio
import json


class GraphqlConnect:
    client = None
    query = ''
    token = ''

    def __init__(self):
        self.client = GraphqlClient(endpoint=hk_graphql['host'])

    def generate_token(self):
        if self.client:
            self.query = """
                mutation {
                    generateAccessToken(data: {
                        email: "{}",
                        password: "{}"
                    })
                }
            """.format(hk_graphql['user_email'], hk_graphql['user_password'])

            print('run generateAccessToken mutation')
            res = asyncio.run(self.client.execute_async(query=self.query))
            if 'data' in res and 'generateAcessToken' in res['data']:
                self.token = res['data']['generateAcessToken']
                print("token: " + self.token)

    def run_query(self, query):
        res = None
        if self.client and query:
            res = asyncio.run(self.client.execute_async(query=query))
        return res

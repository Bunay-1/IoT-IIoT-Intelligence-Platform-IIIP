class GraphQLQueryService:
    def __init__(self, schema):
        self.schema = schema

    def execute_query(self, query):
        print(f"Executing GraphQL query: {query}")
        result = self.schema.execute(query)
        print(f"Query result: {result}")
        return result

    def introspect_schema(self):
        print("Introspecting GraphQL schema")
        schema_info = self.schema.introspect()
        print(f"Schema info: {schema_info}")
        return schema_info

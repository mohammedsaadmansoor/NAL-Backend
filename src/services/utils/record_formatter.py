import json


def format_graph_record(code, name="graph_1"):
    code = json.loads(code)
    if "code" in code:
        code = code['code']
    graph = {"name": name, "type": "graph", "function":code}
    # graph_details.append(graph1)
    # graphs = {"graph_details": graph_details}
    return graph

def format_sql_record(sql_query, name="sql_query_1"):
    sql_query = json.loads(sql_query)
    if "sql_query" in sql_query:
        sql_query = sql_query['sql_query']
    query = {"name": name, "type": "sql_query", "query": sql_query}
    return query

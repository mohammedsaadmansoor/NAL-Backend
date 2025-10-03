import traceback
from src.db.connection import aget_connection, release_connection

async def save_chat(
    conversation_id,
    question,
    sql,
    summary,
    email,
    graph="",
    followUp="",
    host="",
    db="",
    db_user="",
    tables=[],
    sql_result="",
):
    try:
        insert_query = f"""INSERT INTO chat_new (conversation_id, question, sql, summary, email, graph, followup, host, db, db_user,
                selected_tables, sql_result) VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) ON CONFLICT (id) DO 
                UPDATE SET host = $8, db = $9, db_user = $10, selected_tables = $11, sql = $3,
                summary = $4 
                RETURNING id"""
        print(insert_query)
        conn = await aget_connection()
        res = await conn.fetchrow(
            insert_query,
            conversation_id,
            question,
            sql,
            summary,
            email,
            graph,
            ",".join(followUp),
            host,
            db,
            db_user,
            ",".join(tables),
            sql_result,
        )

        # print("res", res)
        await release_connection(conn)
        return res
    except:
        print(traceback.print_exc())
        print("Error while inserting results into database.")
        return ""
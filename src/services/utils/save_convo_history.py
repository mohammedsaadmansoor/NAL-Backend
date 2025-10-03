from fastapi import HTTPException
from src.db.connection import aget_connection, release_connection
import json
from src.settings import settings

class DbError(Exception):
    pass


async def get_sql_query(query, params):
    conn = None
    try:
        conn = await aget_connection()  # Acquire an asynchronous connection
        # Execute the query using asyncpg's fetch method
        print("save convo query 1", query, "save convo param 1", params)

        result = await conn.fetch(query, *params)
        return result
    except Exception as ex:
        print("Error executing select query:", ex)
        raise DbError(f"Error occurred in executing select query!: {ex}")
    finally:
        if conn:
            await release_connection(conn)


# async def get_sql_query2(query, params):
#     conn = None
#     try:

#         conn = await aget_connection2()  # Acquire an asynchronous connection
#         # Execute the query using asyncpg's fetch method
#         print("save convo query", query, "save convo param", params)
#         result = await conn.fetch(query, *params)
#         return result
#     except Exception as ex:
#         print("Error executing select query:", ex)
#         raise DbError(f"Error occurred in executing select query!: {ex}")
#     finally:
#         if conn:
#             await release_connection2(conn)


async def execute_query(query: str, params: tuple):
    conn = None
    try:
        print("inside execute query", "checking")
        conn = await aget_connection()
        # Execute the query
        if query.strip().lower().startswith("select") or query.strip().lower().endswith(
            "returning id"
        ):
            result = await conn.fetch(query, *params)
        else:
            result = await conn.execute(query, *params)
        print("result::: ", result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")
    finally:
        if conn:
            await release_connection(conn)


def extract_summary(text):
    # Look for the word "summary" and extract everything after it
    start_keyword = "``summary``:"

    # Find the index of "``summary``:"
    start_idx = text.lower().find(start_keyword.lower())

    if start_idx == -1:
        return "Summary not found in the text."

    # Extracting the summary part from the start keyword
    summary_part = text[start_idx + len(start_keyword) :].strip()

    # Stop at the next keyword that starts with `` (backticks)
    end_idx = summary_part.find("``")
    if end_idx != -1:
        summary_part = summary_part[:end_idx].strip()

    return summary_part


async def insert_data_collection(body: dict):
    """
    body:
        user_query: str
        response: str
        conversation_id: str
        graphs: json
        sql: json
    """
    try:
        summary = extract_summary(body.get("response"))
        graphs = body.get("graphs", {})
        sql = body.get("sql", {})
        result = await insert_question_details(
            {
                "conversation_id": body.get("conversation_id"),
                "user_query": body.get("user_query"),
                "response": summary,
                "graphs": graphs,
                "sql": sql,
            }
        )
        return result
    except DbError as db_error:
        raise db_error
    except Exception as ex:
        raise Exception(f"Error Occured. {ex}")


async def insert_dashboard_details(body: dict):  # not needed
    """
    body:
        conversation_id
        use_case
        tech_stack
        user_email
    """
    print("adding the info into the dashboard detail table")
    if "use_case_id" not in body:
        body["use_case_id"] = None
    query = f"""INSERT INTO genai_lens.azure_dashboard_details(conversation_id,use_case,tech_stack,user_email) VALUES($1,$2,$3,$4)"""
    try:
        await execute_query(
            query=query,
            params=(
                body.get("conversation_id"),
                body.get("use_case"),
                body.get("tech_stack"),
                body.get("user_email"),
            ),
        )
    except DbError as db_error:
        raise db_error
    except Exception as ex:
        raise Exception(f"Error Occured. {ex}")


async def get_conversation_ids(body: dict):
    """
    body:
        user_email
        tech_stack
        use_case
    """
    try:
        user_email = body.get("email")
        use_case = body.get("use_case")
        tech_stack = body.get("tech_stack")
        print("user_email:: ", user_email, "use_case:: ", use_case, "tech_stack:: ", tech_stack)
        query = f"""select conversation_id, insert_date::date from genai_lens.azure_dashboard_details where user_email=$1 and use_case=$2 and tech_stack=$3 and 
                insert_date::date > (NOW() - INTERVAL '2 days')::date order by insert_date DESC
                """
        result = await get_sql_query(
            query=query,
            params=(
                user_email,
                use_case,
                tech_stack,
            ),
        )
        print("result:: ", result)
        mutable_result = []
        for res in result:
            temp_res = dict(res)
            latest_quest = await get_latest_question(res.get("conversation_id", ""))
            temp_res["latest_quest"] = latest_quest
            if latest_quest != "":
                mutable_result.append(temp_res)
        print("mutable_result:: ", mutable_result)
        return mutable_result
    except:
        print("something went wrong while fetching conversation_ids")
        return []


async def get_latest_question(conversation_id: str):
    query = f"""select user_query from genai_lens.mars_question_details where conversation_id = $1 order by insert_date DESC LIMIT 1"""
    result = await get_sql_query(query=query, params=(conversation_id,))
    if len(result) != 0:
        return result[0]["user_query"]
    return ""


async def insert_question_details(body: dict):
    """
    body:
        conversation_id: str
        user_query: str
        combined_answer: str
        response_json: str

    """
    print("adding the info into the question detail table")
    query = f"""INSERT INTO genai_lens.mars_question_details(conversation_id, user_query, combined_answer, response_json) VALUES($1,$2,$3,$4) returning id"""
    try:
        result = await execute_query(
            query=query,
            params=(
                body.get("conversation_id"),
                body.get("user_query"),
                body.get("combined_answer"),
                body.get("response_json"),
            ),
        )
        return result
    except DbError as db_error:
        raise db_error
    except Exception as ex:
        raise Exception(f"Error Occured. {ex}")


async def get_feedback_history(conversation_id):
    query = f"""Select question_id, conversation_id, feedback_text, star_ratings, created_at from genai_lens.azure_question_feedback where conversation_id=$1"""
    result = await get_sql_query(query=query, params=(conversation_id,))
    return result


async def get_chat_history(conversation_id):
    query = f"""Select id, user_query, combined_answer, response_json from genai_lens.mars_question_details where conversation_id=$1"""
    result = await get_sql_query(query=query, params=(conversation_id,))

    mutable_result = []
    for res in result:
        res_dict = dict(res)
        try:
            if "graphs" in res_dict:
                res_dict["graphs"] = json.loads(res_dict["graphs"])
            if "sql" in res_dict:
                res_dict["sql"] = json.loads(res_dict["sql"])
        except:
            pass
        res_dict["is_history"] = True
        mutable_result.append(res_dict)

    return mutable_result


async def get_conversation_id(conversation_id: str):
    print("conversation_id", conversation_id)
    query = f"""SELECT conversation_id from  genai_lens.mars_question_details WHERE conversation_id=$1"""

    result = await get_sql_query(query=query, params=(conversation_id,))
    #print("@@@@@@@@@@@@@##", result)
    return result

async def save_feedback(body: dict):
    conversation_id = body.get("conversation_id")
    question_id = body.get("question_id")
    feedback_text = body.get("feedback_text")
    star_rating = body.get("star_rating")
    query = f"""INSERT into genai_lens.azure_question_feedback(question_id, conversation_id, feedback_text, star_ratings) VALUES($1, $2, $3, $4)"""

    await execute_query(
        query=query,
        params=(
            question_id,
            conversation_id,
            feedback_text,
            star_rating,
        ),
    )


async def get_session(conversation_id: str):
    query = """SELECT session FROM genai_lens.mars_session_store WHERE conversation_id = $1"""
    result = await get_sql_query(query=query, params=(conversation_id,))
    if len(result) != 0:
        return result[0]['session']
    
    return json.dumps({})

async def save_session(body: dict):
    """
    conversation_id: str
    session: JSONB
    """
    conversation_id = body.get("conversation_id")
    session = body.get("session")
    check_query = """SELECT * from genai_lens.mars_session_store where conversation_id=$1"""
    result = await get_sql_query(query=check_query, params=(conversation_id,))
    
    if len(result) == 0:
        query = """INSERT into genai_lens.mars_session_store(conversation_id, session) VALUES($1, $2)"""
        await execute_query(
            query=query,
            params=(
                conversation_id,
                session
            ),
        )
    else:
        query = """UPDATE genai_lens.mars_session_store SET session=$1 WHERE conversation_id= $2"""
        await execute_query(
            query=query,
            params=(
                session,
                conversation_id
            ),
        )
        
    

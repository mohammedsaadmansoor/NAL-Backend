import base64
from urllib.parse import quote
from src.app.api.azure.tableqa.schema import FileStatus
from src.services.azure.database_v1 import Database_v1
from src.db.connection import aget_connection,get_connection2,aget_connection2, aget_connection_img,release_connection_img,release_connection,release_connection2
from datetime import datetime
import re
from src.utils.logging import get_logger

logger = get_logger(__name__)

async def get_recent_chats_rag_img(conversation_id: str):
    conn = await aget_connection_img(True)
    query  = f"""select * from chatmessage where "threadId" = '{conversation_id}' order by "createdAt" desc LIMIT 20"""
    logger.debug(query)
    chats = await conn.fetch(query)
    await release_connection_img(conn, True)
    logger.debug(len(chats))
    chat_list = []
    i=0
    while(i<len(chats)):
        obj = {}
        if(chats[i]["role"] == "assistant"):
            obj["output"] =  chats[i]["content"]
            j = i + 1
            while(j<len(chats)):
                if(chats[j]["role"] == "user"):
                    obj["input"] = chats[j]["content"]
                    chat_list.append(obj)
                    i=j+1
                    break
                j+=1
        else:
            i+=1
    return chat_list[::-1]


async def get_recent_chats_rag(conversation_id: str):
    conn = await aget_connection()
    query = f"""select * from chatmessage where "threadId" = '{conversation_id}' order by "createdAt" desc LIMIT 20"""
    logger.debug(query)
    chats = await conn.fetch(query)
    await release_connection(conn)
    logger.debug(len(chats))
    chat_list = []
    i = 0
    while i < len(chats):
        obj = {}
        if chats[i]["role"] == "assistant":
            obj["output"] = chats[i]["content"]
            j = i + 1
            while j < len(chats):
                if chats[j]["role"] == "user":
                    obj["input"] = chats[j]["content"]
                    chat_list.append(obj)
                    i = j + 1
                    break
                j += 1
        else:
            i += 1
    return chat_list[::-1]

async def aset_file_status(body : FileStatus):
    [query, params] = get_query_update_file_status(body)
    conn = await aget_connection2()
    logger.info(f"{conn} connection 2")
    await conn.execute(query, *params)
    await release_connection2(conn)

def get_query_update_file_status(body : FileStatus):
    logger.debug(body)
    params = []
    fileIds = []
    now = datetime.now()
    if(body["status"] == "in queue"):
        logger.info("in queue")
        insertParams = []
        placeholders = ""
        i=0
        i+=4
        insertParams += [body["objectIds"]["fileId"], body["vertical"], now, 1]
        string = f"( ${str(i-3)} , ${str(i-2)}, ${str(i-1)}, ${str(i)} ),"
        placeholders += string
        placeholdertext = placeholders[:-1]
        query = f"""INSERT INTO openwiz.file_status (file_url, vertical, created_date, status) VALUES
                {placeholdertext} ON CONFLICT (file_url) DO
                UPDATE SET updated_date = ${str(i+1)}, status = ${str(i+2)} """
        params.extend(insertParams)
        params.extend([now, 1])

        # print(insertParams,"insert params")
        #f"""INSERT INTO openwiz.file_status (file_url, vertical, created_date, status) VALUES
                #{placeholdertext}"""
    elif(body["status"] == "in progress"):
        logger.info("in progress")
        query = f"""UPDATE openwiz.file_status SET updated_date = $1 , status = $2 
                where file_url in ($3) """
        params.extend([now, 2,body["objectIds"]["fileId"]])
    elif(body["status"] == "Learned"):
        logger.info("Learned")
        query = f"""UPDATE openwiz.file_status SET learned_date = $1 , updated_date = $2 , status = $3
                where file_url in ($4) """
        params.extend([now, now, 3,body["objectIds"]["fileId"]])
        logger.info(f"params : {params}")
    elif(body["status"] == "unlearn"):
        query = f"""UPDATE openwiz.file_status SET learned_date = $1 , updated_date = $2 ,
                status = $3 where file_url in ($4) """
        params.extend([None, now, None,body["objectIds"]["fileId"]])
    else:
        query = f"""UPDATE openwiz.file_status SET updated_date = $1 , status = $2 
                where file_url in ($3)"""
        params.extend([now,4,body["objectIds"]["fileId"]])
    logger.debug(query)
    return [query, params]


def get_query_file_status(file : str):
        params = []
        query = f"""Select  status from openwiz.file_status where file_url in ($1) """
        params.extend([file])
        return [query,params]


def set_file_status(body: FileStatus):
    [query, params] = get_query_update_file_status(body)
    pattern = r"\$(\d+)"  # This pattern matches any occurrence of $ followed by digits
    replacement = r"%s"
    # Perform the substitution using re.sub()
    query = re.sub(pattern, replacement, query)
    logger.debug(f"query {tuple(params)}")
    conn = get_connection2()
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()

def get_file_status(file:str):
    [query, params] = get_query_file_status(file)
    pattern = r"\$(\d+)"  # This pattern matches any occurrence of $ followed by digits
    replacement = r"%s"
    # Perform the substitution using re.sub()
    query = re.sub(pattern, replacement, query)
    logger.debug(f"query {tuple(params)}")
    conn = get_connection2()
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result


def format_uri(uri):
    uri = base64.b64decode(uri).decode("utf-8")
    d = uri.split("//")[0]
    uri = uri.split("//")[1]
    p = uri.split(":")
    user = p[0]
    password_host = p[1].split("@")
    password = password_host[0]
    host = password_host[1]
    port = p[2]
    port = port.split("?")[0]
    uri = (
        d + "//" + quote(user) + ":" + quote(password) + "@" + quote(host) + ":" + port
    )
    uri = uri.replace("+psycopg2", "")
    return uri

async def get_table_details(uri, tables, schema="public"):
    db = Database_v1(uri, schema)
    await db.build_engine()
    await db.build_connection()
    table_info = await db.get_table_info_v1(tables)
    sample_rows = await db.include_sample_rows(tables, table_info)
    ans = ""
    for t in sample_rows:
        ans += "\n" + t
    await db.close_connection()
    return ans

def transformConversationStyleToTemperature(style : str):
    
    style_temp_obj = {
        "precise" : 1,
        "balanced" : 0.5,
        "creative" : 0.1
    }
    
    return style_temp_obj.get(style)
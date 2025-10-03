import asyncpg
import psycopg2
import traceback
# from src.config import config
from src.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

DATABASE_PORT = settings.db.POSTGRES_DB_PORT
POSTGRES_PASSWORD = settings.db.POSTGRES_DB_PASSWORD
POSTGRES_USER = settings.db.POSTGRES_DB_USERNAME
POSTGRES_HOST = settings.db.POSTGRES_DB_HOST
POSTGRES_DB_NAME = settings.db.POSTGRES_DB_NAME

def get_connection(
    DATABASE_PORT, POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_DB_NAME, POSTGRES_HOST
):
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=DATABASE_PORT,
        database=POSTGRES_DB_NAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        connect_timeout=20,
    )
    return conn


pool = None
pool2 = None
langchain_pool = None
async def create_db_pool():
    try:
        global pool
        logger.info(f"Creating database connection pool to {POSTGRES_HOST}:{DATABASE_PORT}/{POSTGRES_DB_NAME}")
        
        pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=DATABASE_PORT,
            database=POSTGRES_DB_NAME,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            min_size=1,
            max_size=20,
            max_inactive_connection_lifetime=300,
            timeout=30,
            command_timeout=60,
            server_settings={'application_name': 'nal-backend'} 
        )
        logger.info("Database connection pool created successfully.")
        size = pool.get_size()
        logger.debug(f"Active pool size: {pool._maxsize - pool._queue.qsize()}")
        logger.debug(f"pool_size : {size}")

    except Exception as e:
        logger.error(f"Error while creating database connection pool: {e}")
        logger.error(f"Connection details: host={POSTGRES_HOST}, port={DATABASE_PORT}, db={POSTGRES_DB_NAME}, user={POSTGRES_USER}")
        pool = None
        raise

async def get_pool():
     return pool


async def aget_connection():
    try:
        global pool
        logger.debug(f"pool:: {pool}")
        if pool is None:
            logger.debug("pool is None, creating new pool")
            await create_db_pool()
        
        if pool is None:
            logger.error("Failed to create database pool")
            raise Exception("Database pool creation failed")
            
        logger.debug(f"queue size active: {pool._queue.qsize()}")
        logger.debug(f"Active pool size: {pool._maxsize - pool._queue.qsize()}")
        conn = await pool.acquire()
        if conn is None:
            logger.error("could not get connection from pool")
            raise Exception("Failed to acquire database connection")
        logger.debug("Successfully received a database connection from the connection pool.")
        return conn
    except Exception as e:
        logger.error(f"Error while creating database connection: {e}")
        raise


async def release_connection(conn):
    try:
        global pool
        await pool.release(conn)
        logger.debug("Connection released back to the pool.")
    except Exception as e:
        logger.error(f"Error releasing connection back to the pool: {e}")
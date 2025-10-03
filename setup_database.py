#!/usr/bin/env python3
"""
Database setup script for NAL-Backend.
This script helps set up the PostgreSQL database for development.
"""

import asyncio
import asyncpg
import os
from src.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = await asyncpg.connect(
            host=settings.db.POSTGRES_DB_HOST,
            port=int(settings.db.POSTGRES_DB_PORT),
            user=settings.db.POSTGRES_DB_USERNAME,
            password=settings.db.POSTGRES_DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.db.POSTGRES_DB_NAME
        )
        
        if result:
            logger.info(f"Database '{settings.db.POSTGRES_DB_NAME}' already exists")
        else:
            # Create database
            await conn.execute(f'CREATE DATABASE "{settings.db.POSTGRES_DB_NAME}"')
            logger.info(f"Database '{settings.db.POSTGRES_DB_NAME}' created successfully")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise


async def test_connection():
    """Test database connection."""
    try:
        conn = await asyncpg.connect(
            host=settings.db.POSTGRES_DB_HOST,
            port=int(settings.db.POSTGRES_DB_PORT),
            user=settings.db.POSTGRES_DB_USERNAME,
            password=settings.db.POSTGRES_DB_PASSWORD,
            database=settings.db.POSTGRES_DB_NAME
        )
        
        # Test query
        result = await conn.fetchval("SELECT version()")
        logger.info(f"Database connection successful: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


async def main():
    """Main setup function."""
    logger.info("Starting database setup...")
    
    # Test if PostgreSQL is running
    try:
        conn = await asyncpg.connect(
            host=settings.db.POSTGRES_DB_HOST,
            port=int(settings.db.POSTGRES_DB_PORT),
            user=settings.db.POSTGRES_DB_USERNAME,
            password=settings.db.POSTGRES_DB_PASSWORD,
            database='postgres'
        )
        await conn.close()
        logger.info("PostgreSQL server is running")
    except Exception as e:
        logger.error(f"PostgreSQL server is not accessible: {str(e)}")
        logger.error("Please ensure PostgreSQL is installed and running")
        logger.error("You can install PostgreSQL using:")
        logger.error("  - macOS: brew install postgresql")
        logger.error("  - Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        logger.error("  - Windows: Download from https://www.postgresql.org/download/")
        return
    
    # Create database
    await create_database()
    
    # Test connection
    if await test_connection():
        logger.info("Database setup completed successfully!")
        logger.info("You can now run the application with: poetry run python -m src")
    else:
        logger.error("Database setup failed")


if __name__ == "__main__":
    asyncio.run(main())


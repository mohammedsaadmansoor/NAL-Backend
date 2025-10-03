import asyncio
import os
from pathlib import Path
from src.db.connection import aget_connection, release_connection
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseMigrator:
    """Database migration runner for NAL-Backend."""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "migrations"
    
    async def run_migrations(self) -> None:
        """Run all pending database migrations."""
        try:
            logger.info("Starting database migrations...")
            
            # Get list of migration files
            migration_files = sorted(self.migrations_dir.glob("*.sql"))
            
            if not migration_files:
                logger.info("No migration files found.")
                return
            
            conn = await aget_connection()
            try:
                # Create migrations table if it doesn't exist
                await self._create_migrations_table(conn)
                
                # Run each migration
                for migration_file in migration_files:
                    await self._run_migration(conn, migration_file)
                
                logger.info("All migrations completed successfully.")
                
            finally:
                await release_connection(conn)
                
        except Exception as e:
            logger.error(f"Error running migrations: {str(e)}")
            raise
    
    async def _create_migrations_table(self, conn) -> None:
        """Create migrations tracking table."""
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS nal.migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """
        await conn.execute(create_table_sql)
        logger.debug("Migrations table created or already exists.")
    
    async def _run_migration(self, conn, migration_file: Path) -> None:
        """Run a single migration file."""
        try:
            # Check if migration already executed
            check_sql = "SELECT id FROM nal.migrations WHERE filename = $1"
            result = await conn.fetchrow(check_sql, migration_file.name)
            
            if result:
                logger.debug(f"Migration {migration_file.name} already executed, skipping.")
                return
            
            # Read and execute migration
            logger.info(f"Executing migration: {migration_file.name}")
            
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration
            await conn.execute(migration_sql)
            
            # Record migration as executed
            insert_sql = "INSERT INTO nal.migrations (filename) VALUES ($1)"
            await conn.execute(insert_sql, migration_file.name)
            
            logger.info(f"Migration {migration_file.name} executed successfully.")
            
        except Exception as e:
            logger.error(f"Error executing migration {migration_file.name}: {str(e)}")
            raise


async def run_migrations():
    """Run database migrations."""
    migrator = DatabaseMigrator()
    await migrator.run_migrations()


if __name__ == "__main__":
    asyncio.run(run_migrations())

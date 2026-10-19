"""
MedGraph AI — Neo4j Connection Manager
======================================
Manages Neo4j driver lifecycle, session creation, and connectivity checks.
Decouples database connection configuration from ETL and Graph Agent modules.
"""

import logging
import os
from typing import Optional, Generator
from contextlib import contextmanager

try:
    from neo4j import GraphDatabase, Driver, Session
except ImportError:
    GraphDatabase = None
    Driver = None
    Session = None

logger = logging.getLogger(__name__)

class Neo4jConnectionManager:
    """Manages thread-safe driver creation and session retrieval for Neo4j."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "medgraph123")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver: Optional[Driver] = None

    def get_driver(self) -> Driver:
        """Lazily initialize and return the Neo4j driver instance."""
        if GraphDatabase is None:
            raise ImportError(
                "The 'neo4j' Python package is required. Install it using: pip install neo4j"
            )
            
        if self._driver is None:
            logger.info("Initializing Neo4j driver for %s", self.uri)
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            self._driver.verify_connectivity()
            logger.info("Neo4j connection verified successfully.")
        return self._driver

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager yielding a Neo4j session."""
        driver = self.get_driver()
        session = driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()

    def close(self) -> None:
        """Close the driver instance and free resources."""
        if self._driver is not None:
            logger.info("Closing Neo4j driver connection.")
            self._driver.close()
            self._driver = None


# ---------------------------------------------------------------------------
# Module-level singleton — shared across all agents and API routes
# ---------------------------------------------------------------------------
_connection_manager: Optional[Neo4jConnectionManager] = None


def get_connection_manager() -> Neo4jConnectionManager:
    """Return the shared Neo4jConnectionManager singleton."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = Neo4jConnectionManager()
    return _connection_manager


def get_driver():
    """
    Convenience function: return the Neo4j driver from the singleton manager.

    Usage (in agents and API):
        from connection import get_driver
        driver = get_driver()
        with driver.session() as session: ...
    """
    return get_connection_manager().get_driver()

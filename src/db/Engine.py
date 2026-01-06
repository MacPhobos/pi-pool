"""SQLAlchemy engine singleton for PiPool database connections."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator


class Engine:
    """Singleton database engine and session factory.

    Manages SQLAlchemy engine and session lifecycle. Accepts config
    parameters in constructor to avoid circular dependency with Config.py.
    """

    __instance = None

    @staticmethod
    def getInstance():
        """Static access method."""
        if Engine.__instance is None:
            raise Exception("Engine not instantiated. Call Engine(config) first.")
        return Engine.__instance

    def __init__(self, dbName: str, dbUser: str, dbPassword: str, dbHost: str = "localhost"):
        """Initialize database engine with connection parameters.

        Args:
            dbName: Database name
            dbUser: Database user
            dbPassword: Database password
            dbHost: Database host (default: localhost)

        Raises:
            Exception: If singleton already initialized
        """
        if Engine.__instance is not None:
            raise Exception("Engine singleton already initialized")

        # Build connection URL
        connectionUrl = f"postgresql://{dbUser}:{dbPassword}@{dbHost}/{dbName}"

        # Create engine
        self.engine = create_engine(
            connectionUrl,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,  # Verify connections before using
        )

        # Create session factory
        self.SessionFactory = sessionmaker(bind=self.engine)

        logging.info(f"Database engine initialized: {dbName}@{dbHost}")

        Engine.__instance = self

    @contextmanager
    def getSession(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.

        Yields:
            SQLAlchemy session

        Example:
            with engine.getSession() as session:
                session.add(model)
                session.commit()
        """
        session = self.SessionFactory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logging.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()

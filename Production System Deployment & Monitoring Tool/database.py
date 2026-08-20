import os
import logging
import urllib.parse
import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
load_dotenv()

logger = logging.getLogger("monitoring.database")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "production_monitoring")

# URL-encode credentials to safely handle special characters like '@'
encoded_user = urllib.parse.quote_plus(DB_USER)
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

DATABASE_URL = f"mysql+pymysql://{encoded_user}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Declarative Base for SQLAlchemy ORM models
Base = declarative_base()

# Initialize SQLAlchemy engine & SessionLocal
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_url() -> str:
    """Returns the configured MySQL connection URL."""
    return DATABASE_URL


def init_database():
    """
    Initializes the MySQL database and SQLAlchemy engine:
    1. Connects to MySQL server to ensure DB_NAME database exists (CREATE DATABASE IF NOT EXISTS).
    2. Verifies SQLAlchemy Engine connection.
    3. Creates all registered ORM tables if they do not already exist.
    """
    global engine, SessionLocal

    # Step 1: Ensure database exists
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            connection.commit()
            logger.info(f"Database '{DB_NAME}' verified/created successfully.")
        finally:
            connection.close()
    except Exception as e:
        logger.warning(
            f"Could not automatically create database '{DB_NAME}'. "
            f"If the database does not exist, please create it manually using: "
            f"'CREATE DATABASE {DB_NAME};'. Error: {str(e)}"
        )

    # Step 2: Create tables from metadata
    Base.metadata.create_all(bind=engine)
    logger.info("All database tables verified and created successfully.")
    return engine


def get_db():
    """
    FastAPI dependency for obtaining a database session per request.
    Yields session and guarantees cleanup on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

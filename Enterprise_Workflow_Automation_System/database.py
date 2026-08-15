import os
import logging
import urllib.parse
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("workflow_database")
logging.basicConfig(level=logging.INFO)

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Takdir@1234")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME", "enterprise_workflow")

encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"
SQLITE_URL = os.getenv("SQLITE_DATABASE_URL", "sqlite:///./workflow.db")

def auto_create_mysql_db():
    """Automatically create the MySQL database if MySQL server is online."""
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        connection.commit()
        connection.close()
        logger.info(f"MySQL database '{MYSQL_DB_NAME}' verified/created successfully.")
        return True
    except Exception as e:
        logger.warning(f"MySQL connection check ({e}). Using SQLite fallback.")
        return False

def init_engine():
    # Attempt MySQL auto-create first
    if auto_create_mysql_db():
        try:
            engine = create_engine(MYSQL_URL, pool_pre_ping=True, echo=False)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to MySQL database engine!")
            return engine
        except Exception as e:
            logger.warning(f"MySQL engine connect failed ({e}). Falling back to SQLite database.")

    logger.info("Using SQLite fallback database ('workflow.db').")
    engine = create_create_sqlite_engine()
    return engine

def engine_create_sqlite_engine():
    return create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

def create_create_sqlite_engine():
    return create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

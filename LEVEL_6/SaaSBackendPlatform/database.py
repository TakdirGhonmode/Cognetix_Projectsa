from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# Handle SQLite vs MySQL / PostgreSQL configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Attempt connecting to MySQL, fallback gracefully to SQLite if MySQL is offline locally
db_url = settings.DATABASE_URL
try:
    if db_url.startswith("mysql"):
        test_engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        with test_engine.connect() as conn:
            pass
        engine = test_engine
    else:
        engine = create_engine(db_url, connect_args=connect_args, echo=False)
except Exception as e:
    print(f"[!] Unable to connect to MySQL database at {db_url}. Falling back to SQLite local database.")
    fallback_url = "sqlite:///./saas.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for obtaining database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

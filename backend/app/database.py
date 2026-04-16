from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import normalized_database_url


engine_kwargs = {"pool_pre_ping": True}
db_url = normalized_database_url()
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

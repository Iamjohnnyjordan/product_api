from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

#DATABASE_URL - WHERE is my database?
DATABASE_URL = "sqlite:///./products.db"

#engine      HOW does SQLAlchemy communicate with it?
engine = create_engine(DATABASE_URL)

#SessionLocal   HOW will I create sessions to work with it?
SessionLocal = sessionmaker(bind=engine)

#Base           → WHAT will my database model classes inherit from?
class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


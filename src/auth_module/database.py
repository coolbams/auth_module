from sqlalchemy import create_engine, text
from sqlalchemy.orm import session, sessionmaker, DeclarativeBase

from auth_module.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
def check_db():
    try: 
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
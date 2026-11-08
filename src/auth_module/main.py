from fastapi import FastAPI, HTTPException, Request



from auth_module.database import Base, engine, check_db
from auth_module import models
from auth_module.router import router as auth_router

import logging
from applog import setup_logging
from applog.middleware import RequestLoggingMiddleware

setup_logging(level="INFO", log_dir="logs")

log = logging.getLogger(__name__)

if not check_db():
    log.error("Cannot reach the database.")
    raise SystemExit("Cannot reach the database. Is Docker running? (docker compose up -d)")
Base.metadata.create_all(engine)

app = FastAPI(title="Auth module")
app.include_router(auth_router)

app.add_middleware(RequestLoggingMiddleware)



@app.get("/health")
def health():
    
    if not check_db():
        log.error("Database unreachable")
        raise HTTPException(503, "Database unreachable")
    
    return {
        "message" : "Backend up and running",
        "status": "ok", "db": "connected"
        }
    
    
    
    
    
    
    
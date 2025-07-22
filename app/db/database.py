from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

# For synchronous operations
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://echolist:echolist_password@localhost:5435/echolist"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# For asynchronous operations
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL", 
    "postgresql+asyncpg://echolist:echolist_password@localhost:5435/echolist"
)
async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False, 
    bind=async_engine
)

Base = declarative_base()

# Dependency for synchronous operations
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency for asynchronous operations
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings, BASE_DIR

class Base(DeclarativeBase):
    pass

def resolve_db_url(url: str) -> str:
    # Ensure relative SQLite URLs resolve consistently against backend BASE_DIR
    if "sqlite" in url and ":///./" in url:
        driver_prefix = url.split(":///./")[0]
        rel_path = url.split(":///./")[-1]
        abs_path = (BASE_DIR / rel_path).resolve().as_posix()
        return f"{driver_prefix}:///{abs_path}"
    return url

db_url = resolve_db_url(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

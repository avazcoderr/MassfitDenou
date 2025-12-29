import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Try to load a .env from project root first, fall back to a local .env next to this file
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    local_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(local_env):
        load_dotenv(local_env)

# Do NOT import DATABASE_URL from app.config here - read from env to avoid using a wrong value
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Normalize Railway/Heroku-style URLs to asyncpg for SQLAlchemy async engine
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Helpful log line (visible in Railway deploy logs)
print("DATABASE_URL used for engine:", DATABASE_URL.split("://", 1)[0] + "://...")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:  # type: ignore
    async with async_session_maker() as session:
        yield session

# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

from shared.logger.logger import get_logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.config import Settings

logger = get_logger("db.setup")

async_eng = create_async_engine(
    Settings.ASYNC_POSTGRES_URL,
    pool_size=6,
    max_overflow=5,
    pool_timeout=30,
    pool_pre_ping=True,
)

AsyncLocal = async_sessionmaker(
    bind=async_eng, class_=AsyncSession, expire_on_commit=False
)


async def get_session():
    async with AsyncLocal() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise


async def close_async_engine():
    await async_eng.dispose()


async def connection_check():
    try:
        async with async_eng.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(msg="✅ Successfully connected to the database!")
    except Exception as e:
        logger.error(msg=f"❌ Error connecting to database: {e}")

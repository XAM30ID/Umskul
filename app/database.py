import os
from typing import Annotated
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import Depends
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_db)]

class Base(DeclarativeBase):
    pass

async def setup_database():
    '''
        Функция созданя базы данных
    '''
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
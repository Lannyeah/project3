from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine_test = create_async_engine("sqlite+aiosqlite:///:memory:")
Async_Session_Test = async_sessionmaker(bind=engine_test, expire_on_commit=False)

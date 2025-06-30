from app.database import engine


#async def __init_models__(): #Ручное создание таблиц без миграций
#    async with engine.begin() as conn:
#        await conn.run_sync(Base.metadata.create_all)
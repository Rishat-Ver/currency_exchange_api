from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api import router
from app.core import sessionmanager
from app.utils.currencies import fetch_currency_data


@asynccontextmanager
async def lifespan(app: FastAPI, aioredis=None):
    await fetch_currency_data()
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)

# admin = Admin(
#     app=app,
#     session_maker=sessionmanager.session_maker,
#     authentication_backend=AdminAuth(settings.AUTH.KEY),
# )
# admin.add_view(UserModelView)
# admin.add_view(TaskModelView)
# admin.add_view(UserTasksAssociationModelView)
# app.include_router(router)
# app.include_router(admin_router)
# add_pagination(app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8066,
        reload=True,
        workers=3,
    )

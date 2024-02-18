from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqladmin import Admin

from app.api import router
from app.api.admin.model import UserModelView
from app.core import sessionmanager
from app.utils.currencies import fetch_currency_data
from app.api.admin.model import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI, aioredis=None):
    await fetch_currency_data()
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)

admin = Admin(
    app=app,
    session_maker=sessionmanager.session_maker,
)
admin.add_view(UserModelView)
app.include_router(admin_router)
# add_pagination(app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8066,
        reload=True,
        workers=3,
    )

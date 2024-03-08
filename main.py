from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqladmin import Admin

from app.api import router
from app.api.admin.model import AdminAuth, BalanceModelView, UserModelView
from app.api.admin.model import router as admin_router
from app.core import sessionmanager
from app.core.config import settings
from app.exceptions import (BadRequestException, CustomException,
                            custom_exception_handler,
                            request_exception_handler)
from app.services import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI, aioredis=None):
    await RedisClient.fetch_currency_data()
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)

app.add_exception_handler(BadRequestException, request_exception_handler)
app.add_exception_handler(CustomException, custom_exception_handler)

admin = Admin(
    app=app,
    session_maker=sessionmanager.session_maker,
    authentication_backend=AdminAuth(settings.AUTH.KEY),
)
admin.add_view(UserModelView)
admin.add_view(BalanceModelView)
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

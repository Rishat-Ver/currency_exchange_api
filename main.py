from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core import sessionmanager


@asynccontextmanager
async def lifespan(app: FastAPI, aioredis=None):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)


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
        reload=True,
        workers=3,
    )

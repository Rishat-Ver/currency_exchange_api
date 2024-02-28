from fastapi import APIRouter
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.api.auth.security import verify_password, create_access_token
from app.api.models import User
from app.core import sessionmanager
from app.core.config import settings

router = APIRouter(include_in_schema=False)


class UserModelView(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.created_at,
        User.balance,
        User.currency,
        User.is_admin,
    ]
    column_sortable_list = [User.id]
    column_searchable_list = [User.username, User.currency]


class AdminAuth(AuthenticationBackend):
    """Вход в админку разрешен только админам."""

    async def login(self, request: Request) -> bool:
        async with sessionmanager.session() as session:
            form = await request.form()
            username = form["username"]
            password = form["password"]

            stmt = select(User).filter(User.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user and verify_password(password, user.password) and user.is_admin:
                request.session.update(
                    {
                        "token": create_access_token(
                            data={"user_id": user.id, "token_type": "Bearer"}
                        )
                    }
                )
                return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True


@router.post("/login")
async def login(request: Request):
    auth_backend = AdminAuth(settings.AUTH.KEY)
    await auth_backend.login(request)

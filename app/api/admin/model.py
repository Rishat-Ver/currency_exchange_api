from fastapi import APIRouter
from sqladmin import ModelView

from app.api.models import User

router = APIRouter(include_in_schema=False)


class UserModelView(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.created_at,
        User.balance,
        User.currency,
    ]
    column_sortable_list = [User.id]
    column_searchable_list = [User.username, User.currency]

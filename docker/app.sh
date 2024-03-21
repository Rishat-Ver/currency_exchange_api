#!/usr/bin/bash

export PYTHONPATH=/currency_exchange_api/:$PYTHONPATH

#alembic revision --autogenerate -m 'create tables'
alembic upgrade head

python app/commands/createsuperuser.py --username=admin --password=admin --email=admin@ya.ru

uvicorn main:app --host 0.0.0.0 --port 8000
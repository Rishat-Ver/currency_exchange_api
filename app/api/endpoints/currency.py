from datetime import datetime

import aiohttp
from fastapi import APIRouter, Depends

from app.api.models import User
from app.api.schemas import ResponseCurrency
from app.core.config import settings
from app.utils.users import get_current_user

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/exchange_rate")
async def get_exchange_rates(
        source: str = 'USD', currencies: str = None
):
    a = currencies.split(',')
    curren = '%2C'.join(a) if len(a) > 1 else a[0]
    url = f"{settings.API.EXCRATES}?source={source}&currencies={currencies}"
    headers = {"apikey": settings.API.KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                response = ResponseCurrency(
                    time=datetime.utcfromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    source=data['source'],
                    quotes=data['quotes']
                    )

    return response




# {'success': True, 'timestamp': 1707944163, 'source': 'USD', 'quotes': {'USDEUR': 0.93219, 'USDRUB': 91.650152}}
# datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
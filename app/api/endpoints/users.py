import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
from fastapi_limiter.depends import RateLimiter
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User
from app.api.schemas import BalanceSchema, ResponseUserBalance
from app.core.database import get_db_session
from app.exceptions import BadRequestException
from app.services import RedisClient
from app.services.websocket_manager import websocket_, ws_manager
from app.utils.balances import find_or_create_balance
from app.utils.currencies import check_currencies, get_exchange
from app.utils.send_email import send_email_async
from app.utils.users import (
    check_password_and_username,
    create_response_user_balance,
    get_current_user,
)

router = APIRouter(prefix="/users", tags=["Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pass(password: str):
    return pwd_context.hash(password)


@router.websocket("/ws/")
async def websocket_endpoint_users(
    websocket: WebSocket, session=Depends(get_db_session)
):
    await websocket_(websocket, session)


@router.post("/create", status_code=status.HTTP_201_CREATED)
@check_password_and_username
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    image: UploadFile = File(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Создает нового пользователя с предоставленными учетными данными и изображением профиля.

    Этот эндпойнт принимает обязательные поля: username, password и email, а также
    необязательное поле image для загрузки изображения профиля. Если изображение не
    предоставлено, будет использовано стандартное изображение профиля.

    Параметры:
    - username (str): Желаемое имя пользователя, должно быть буквенно-цифровым и начинаться с заглавной буквы.
    - password (str): Пароль для аккаунта, должен содержать минимум 8 символов, включать в себя
                      заглавные и строчные буквы, а также цифры.
    - email (str): Электронная почта пользователя.
    - image (UploadFile, optional): Файл изображения профиля пользователя. Допустимые форматы: .jpg, .jpeg, .png.

    Возвращает:
    - user (User): Объект пользователя с информацией о новом аккаунте.

    Вызывает HTTPException со статусом 400 Bad Request, если входные данные не проходят валидацию.

    """

    save_dir = Path("app/media")
    save_dir.mkdir(exist_ok=True)
    if image:
        image_type = image.filename.split(".")[-1]
        file_extension = image_type if image_type in ("jpg", "jpeg", "png") else None
        if not file_extension:
            return JSONResponse(
                status_code=400, content={"message": "Invalid file format"}
            )
        save_path = save_dir / f"{username}.{file_extension}"
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    else:
        save_path = Path("app/media/profile.png")
    hash_password = hash_pass(password)
    new_user = User(
        username=username,
        password=hash_password,
        email=email,
        image_path=str(save_path),
    )
    session.add(new_user)
    await session.commit()
    return new_user


@router.get("/me", response_model=ResponseUserBalance)
async def get_me(user: User = Depends(get_current_user)):
    """
    Получение данных о текущем пользователе и его балансе.

    Этот эндпоинт предназначен для получения информации о профиле текущего пользователя,
    включая его баланс в различных валютах. Пользователь идентифицируется по токену аутентификации,
    который должен быть предоставлен в заголовках запроса.

    Возвращает:
    - response (ResponseUserBalance): Объект, содержащий информацию о пользователе и его балансах.

    Требуется аутентификация.
    """

    response = await create_response_user_balance(user)
    return response


@router.patch("/top_up_balance/", response_model=ResponseUserBalance)
async def update_balance(
    balance: BalanceSchema,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Пополнение баланса текущего пользователя.

    Пользователь может пополнить свой баланс в выбранной валюте. Этот запрос требует передачи
    объекта BalanceSchema, который содержит информацию о валюте и сумме пополнения.

    Параметры:
    - balance (BalanceSchema): Схема данных баланса с валютой и суммой пополнения.
    - background_tasks (BackgroundTasks): Задачи, выполняемые в фоне после завершения запроса.
    - user (User): Авторизованный пользователь, для которого будет пополнен баланс.
    - session (AsyncSession): Сессия подключения к базе данных.

    Возвращает:
    - response (ResponseUserBalance): Объект с обновленной информацией о балансе пользователя.

    Вызывает BadRequestException, если предоставленная валюта не поддерживается.

    После успешного пополнения баланса в фоне отправляется email-уведомление пользователю
    и через WebSocket передается сообщение о пополнении.

    Требуется аутентификация.
    """

    cache = await RedisClient.get_currency("currencies")

    if balance.currency not in cache:
        raise BadRequestException(detail="Incorrect currency")

    existing_balance = next(
        (b for b in user.balances if b.currency == balance.currency), None
    )
    if existing_balance:
        existing_balance.amount += balance.amount
    else:
        await find_or_create_balance(
            session=session,
            user_id=user.id,
            currency=balance.currency,
            amount=balance.amount,
        )

    await session.commit()
    await session.refresh(user)
    background_tasks.add_task(
        send_email_async,
        f"adding funds to your account",
        f"Your balance has been successfully replenished with {balance.amount} {balance.currency}",
        user.email,
    )
    await ws_manager.send_to_user(
        user.id,
        message=f"Your balance has been successfully replenished with {balance.amount} {balance.currency}",
    )
    response = await create_response_user_balance(user)
    return response


@router.patch("/change_currency/", response_model=ResponseUserBalance)
@check_currencies
async def convert_user_currency(
    request: Request,
    background_tasks: BackgroundTasks,
    source: str = Query(
        description="Currency you are converting from",
        example="USD",
        min_length=3,
        max_length=3,
    ),
    currency: str = Query(
        description="Currency you are converting to",
        example="EUR",
        min_length=3,
        max_length=3,
    ),
    amount: float = Query(description="The amount to be converted.", gt=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Конвертация валютного баланса пользователя из одной валюты в другую.

    Этот эндпоинт позволяет пользователю конвертировать указанную сумму средств из одной валюты (source)
    в другую валюту (target) по текущему обменному курсу. Операция конвертации изменяет баланс
    пользователя в обеих валютах и включает в себя отправку уведомления по электронной почте о совершенной транзакции.

    Параметры запроса:
    - source (str): Трехбуквенный код валюты, из которой будет производиться конвертация.
    - target (str): Трехбуквенный код валюты, в которую будет производиться конвертация.
    - amount (float): Сумма в валюте source, которую пользователь хочет конвертировать.

    Ответ:
    - Объект с информацией о балансе пользователя после конвертации (ResponseUserBalance).

    При неудачной попытке конвертации, если пользователь не имеет достаточного баланса в валюте source
    или не имеет валюты source вовсе, будет вызвано исключение BadRequestException.

    После успешной конвертации в фоновом режиме отправляется email-уведомление пользователю
    и через WebSocket передается сообщение о совершенной транзакции.

    Требуется аутентификация.
    """

    source_balance = next((b for b in user.balances if b.currency == source), None)
    if not source_balance:
        raise BadRequestException(detail="You don't have this currency")

    if source_balance.amount < amount:
        raise BadRequestException(detail="Insufficient funds")

    exchange = await get_exchange(source=source, currencies=[currency])
    exchange_rate = exchange["quotes"][f"{source}{currency}"]

    target_balance = await find_or_create_balance(session, user.id, currency)
    source_balance.amount -= amount
    add_amount = round(amount * exchange_rate, 2)
    target_balance.amount += add_amount

    if source_balance.amount == 0:
        await session.delete(source_balance)

    await session.commit()
    await session.refresh(user)
    background_tasks.add_task(
        send_email_async,
        f"Convert currency",
        f"you exchanged {amount} {source} for {add_amount} {currency}",
        user.email,
    )
    await ws_manager.send_to_user(
        user.id,
        message=f"you exchanged {amount} {source} for {add_amount} {currency}",
    )
    response = await create_response_user_balance(user)
    return response


@router.delete("/me/delete", status_code=status.HTTP_204_NO_CONTENT)
async def user_delete(
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Удаление аккаунта текущего пользователя.

    Этот эндпоинт позволяет текущему аутентифицированному пользователю удалить свой аккаунт.
    Удаление производится из базы данных, и в фоновом режиме пользователю отправляется
    электронное письмо с уведомлением об удалении аккаунта.

    Зависимости:
    - background_tasks (BackgroundTasks): Инструмент для выполнения фоновых задач.
    - user (User): Текущий пользователь, полученный из зависимости get_current_user.
    - session (AsyncSession): Сессия базы данных для выполнения транзакций.

    В случае успеха возвращает статус 204 OK без тела ответа.

    Требуется аутентификация.
    """

    await session.delete(user)
    await session.commit()
    background_tasks.add_task(
        send_email_async,
        f"delete account",
        f"your account successfully delete",
        user.email,
    )


@router.get(
    "/evaluate_balance", dependencies=[Depends(RateLimiter(times=1, seconds=5))]
)
@check_currencies
async def evaluate_balance_to_only_currency(
    source: str = Query(
        description="Currency you are converting to",
        example="EUR",
        min_length=3,
        max_length=3,
    ),
    user: User = Depends(get_current_user),
):
    """
    Конвертация и оценка общего капитала пользователя в указанной валюте.

    Этот эндпоинт позволяет пользователю оценить суммарный баланс всех его валютных балансов,
    конвертированный в выбранную валюту (source). Валютный курс для конвертации
    получается через внешний сервис обмена валют.

    Параметры:
    - source (str): Трехбуквенный код валюты (например, 'EUR'), в которую будет
                    конвертирован и показан общий капитал пользователя.
    - user (User): Текущий пользователь, полученный из зависимости get_current_user.

    Возвращает:
    - Строка с оценкой общего капитала пользователя в указанной валюте.

    Эндпоинт ограничен по частоте запросов (rate-limited) до 1 запроса в 5 секунд.

    Требуется аутентификация.
    """

    user_currencies = [i.currency for i in user.balances]
    exchange = await get_exchange(source=source, currencies=user_currencies)

    rates_user_currencies = {
        f"{code[3:]}": rate for code, rate in exchange["quotes"].items()
    }

    result = sum(
        balance.amount / rates_user_currencies.get(balance.currency, 1)
        for balance in user.balances
        if balance.currency in rates_user_currencies
        or balance.currency == source.upper()
    )

    return f"Your capital in {source} is {round(result, 2)} {source}"

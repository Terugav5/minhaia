# discord_bot/utils/db_session.py

from functools import wraps
from sqlalchemy.orm import Session
from database.database import get_db


def db_session_decorator(func):
    """
    Um decorador que injeta uma sessão do banco de dados (`db`)
    nos `kwargs` da função decorada e garante que a sessão seja fechada.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        db: Session = next(get_db())
        try:
            # Adiciona a sessão do db aos argumentos da função
            kwargs["db"] = db
            return await func(*args, **kwargs)
        finally:
            db.close()

    return wrapper

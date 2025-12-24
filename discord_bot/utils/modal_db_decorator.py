# discord_bot/utils/modal_db_decorator.py

from functools import wraps
from sqlalchemy.orm import Session
from database.database import get_db

def modal_db_session_decorator(on_submit_method):
    """
    Um decorador para o método on_submit de um Modal que injeta uma sessão
    do banco de dados (`db`) e garante que a sessão seja fechada.
    """
    @wraps(on_submit_method)
    async def wrapper(self, interaction, *args, **kwargs):
        db: Session = next(get_db())
        try:
            # Chamar o método on_submit original com a sessão do db
            return await on_submit_method(self, interaction, db=db, *args, **kwargs)
        finally:
            db.close()
    return wrapper

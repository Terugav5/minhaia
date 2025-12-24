# discord_bot/database/models.py

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    BigInteger,
    Boolean,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .database import Base
import datetime


class User(Base):
    """Modelo de usuário para armazenar informações sobre os membros do Discord."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(BigInteger, unique=True, index=True, nullable=False)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    coins = Column(Integer, default=0)


class GuildConfig(Base):
    """Modelo para armazenar as configurações específicas de cada servidor."""

    __tablename__ = "guild_configs"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, unique=True, index=True, nullable=False)

    # IDs dos cargos
    analyst_role_id = Column(BigInteger, nullable=True)
    mediator_role_id = Column(BigInteger, nullable=True)
    support_role_id = Column(BigInteger, nullable=True)
    blacklist_role_id = Column(BigInteger, nullable=True)

    # IDs dos canais de log
    general_log_channel_id = Column(BigInteger, nullable=True)
    matches_log_channel_id = Column(BigInteger, nullable=True)
    mediator_log_channel_id = Column(BigInteger, nullable=True)

    # Canal do painel de mediadores
    mediator_panel_channel_id = Column(BigInteger, nullable=True)

    # Configurações de Ticket
    ticket_category_id = Column(BigInteger, nullable=True)
    ticket_channel_id = Column(BigInteger, nullable=True)

    # Canal de Ranking
    ranking_channel_id = Column(BigInteger, nullable=True)


class TicketOption(Base):
    """Modelo para as opções do select menu de tickets."""
    __tablename__ = "ticket_options"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, ForeignKey("guild_configs.guild_id"), nullable=False)
    label = Column(String, nullable=False)
    description = Column(String, nullable=True)

class Match(Base):
    """Modelo para armazenar informações sobre as partidas."""

    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, nullable=False)
    channel_id = Column(BigInteger, unique=True, nullable=False)
    message_id = Column(BigInteger, unique=True, nullable=False)
    status = Column(String, default="pending")  # pending, confirmed, finished
    players = relationship("MatchTeamPlayer", back_populates="match", cascade="all, delete-orphan")


class MatchTeamPlayer(Base):
    """Tabela de associação para jogadores em uma partida, indicando time e status de confirmação."""
    __tablename__ = "match_team_players"
    match_id = Column(Integer, ForeignKey("matches.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    team_number = Column(Integer, primary_key=True)  # 1 ou 2
    confirmed = Column(Boolean, default=False)

    match = relationship("Match", back_populates="players")
    user = relationship("User")


class Mediator(Base):
    """Modelo para armazenar informações sobre os mediadores, incluindo a chave PIX."""

    __tablename__ = "mediators"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pix_key = Column(String, unique=True, nullable=True)
    user = relationship("User")


class Blacklist(Base):
    """Modelo para armazenar usuários na blacklist."""

    __tablename__ = "blacklist"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    moderator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", foreign_keys=[user_id])
    moderator = relationship("User", foreign_keys=[moderator_id])


class Queue(Base):
    """Modelo para representar uma fila de espera em um canal."""
    __tablename__ = "queues"
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(BigInteger, unique=True, nullable=False)
    message_id = Column(BigInteger, unique=True, nullable=False)
    queue_type = Column(String, nullable=False)
    players = relationship("QueuePlayer", back_populates="queue", cascade="all, delete-orphan")

class QueuePlayer(Base):
    """Tabela de associação para jogadores em uma fila."""
    __tablename__ = "queue_players"
    queue_id = Column(Integer, ForeignKey("queues.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    queue = relationship("Queue", back_populates="players")
    user = relationship("User")


class Price(Base):
    """Modelo para armazenar os preços das partidas configurados por servidor."""

    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, ForeignKey("guild_configs.guild_id"), nullable=False)
    match_type = Column(String, nullable=False)  # Ex: "1v1", "2v2", "4v4"
    price = Column(Integer, nullable=False)


class EmbedConfig(Base):
    """Modelo para armazenar as configurações das embeds das filas."""

    __tablename__ = "embed_configs"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, ForeignKey("guild_configs.guild_id"), nullable=False)
    queue_type = Column(String, nullable=False)  # Ex: "Mobile_1v1", "Emulador_4v4"
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    color = Column(String, nullable=True)
    footer = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

# discord_bot/utils/logger.py

import discord
from discord.ext import commands
from database.models import GuildConfig
from sqlalchemy.orm import Session


async def log_action(
    bot: commands.Bot,
    db: Session,
    guild_id: int,
    log_type: str,
    embed: discord.Embed,
):
    """
    Envia uma mensagem de log para o canal apropriado.
    log_type pode ser 'general', 'matches', ou 'mediator'.
    """
    guild_config = db.query(GuildConfig).filter(GuildConfig.guild_id == guild_id).first()
    if not guild_config:
        return

    channel_id = None
    if log_type == "general":
        channel_id = guild_config.general_log_channel_id
    elif log_type == "matches":
        channel_id = guild_config.matches_log_channel_id
    elif log_type == "mediator":
        channel_id = guild_config.mediator_log_channel_id

    if channel_id:
        try:
            channel = await bot.fetch_channel(channel_id)
            await channel.send(embed=embed)
        except discord.NotFound:
            print(f"Canal de log {log_type} com ID {channel_id} não encontrado.")
        except discord.Forbidden:
            print(
                f"Não tenho permissão para enviar mensagens no canal de log {log_type} (ID: {channel_id})."
            )

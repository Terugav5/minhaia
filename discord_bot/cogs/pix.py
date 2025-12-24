# discord_bot/cogs/pix.py

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Mediator, GuildConfig, User
from utils.db_session import db_session_decorator
from utils.modal_db_decorator import modal_db_session_decorator


class PixModal(discord.ui.Modal, title="Registrar Chave PIX"):
    pix_key_input = discord.ui.TextInput(
        label="Sua Chave PIX",
        placeholder="Digite sua chave PIX aqui...",
        style=discord.TextStyle.short,
    )

    def __init__(self, user: discord.User):
        super().__init__()
        self.user = user

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        # Garante que o usuário exista na tabela de usuários
        db_user = db.query(User).filter(User.discord_id == self.user.id).first()
        if not db_user:
            db_user = User(discord_id=self.user.id)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        # Atualiza ou cria o registro do mediador
        mediator = db.query(Mediator).filter(Mediator.user_id == db_user.id).first()
        if not mediator:
            mediator = Mediator(user_id=db_user.id, pix_key=self.pix_key_input.value)
            db.add(mediator)
        else:
            mediator.pix_key = self.pix_key_input.value
        db.commit()
        await interaction.response.send_message(
            "Chave PIX registrada com sucesso!", ephemeral=True
        )


class PixCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pix", description="Registre sua chave PIX para atuar como mediador.")
    @db_session_decorator
    async def pix(self, interaction: discord.Interaction, db: Session):
        """
        Permite que mediadores registrem ou atualizem sua chave PIX.
        """
        guild_config = (
            db.query(GuildConfig)
            .filter(GuildConfig.guild_id == interaction.guild.id)
            .first()
        )

        if (
            not guild_config
            or not guild_config.mediator_role_id
            or not any(
                role.id == guild_config.mediator_role_id
                for role in interaction.user.roles
            )
        ):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
            return

        modal = PixModal(user=interaction.user)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(PixCog(bot))

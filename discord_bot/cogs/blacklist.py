# discord_bot/cogs/blacklist.py

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session
from ..database.database import get_db
import discord
from ..database.models import Blacklist, GuildConfig, User
from ..utils.db_session import db_session_decorator
from ..utils.modal_db_decorator import modal_db_session_decorator
from ..utils.logger import log_action


class BlacklistModal(discord.ui.Modal, title="Adicionar Usuário à Blacklist"):
    user_id_input = discord.ui.TextInput(
        label="ID do Usuário",
        placeholder="Cole o ID do usuário do Discord aqui...",
        style=discord.TextStyle.short,
    )
    reason_input = discord.ui.TextInput(
        label="Motivo",
        placeholder="Digite o motivo para adicionar à blacklist...",
        style=discord.TextStyle.long,
    )

    def __init__(self, moderator: discord.User):
        super().__init__()
        self.moderator = moderator

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        try:
            user_id = int(self.user_id_input.value)
            # Garante que o usuário exista na tabela de usuários
            db_user = db.query(User).filter(User.discord_id == user_id).first()
            if not db_user:
                db_user = User(discord_id=user_id)
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            # Garante que o moderador exista na tabela de usuários
            db_moderator = (
                db.query(User).filter(User.discord_id == self.moderator.id).first()
            )
            if not db_moderator:
                db_moderator = User(discord_id=self.moderator.id)
                db.add(db_moderator)
                db.commit()
                db.refresh(db_moderator)

            # Adiciona o usuário à blacklist
            new_blacklist_entry = Blacklist(
                user_id=db_user.id,
                reason=self.reason_input.value,
                moderator_id=db_moderator.id,
            )
            db.add(new_blacklist_entry)
            db.commit()

            # Log da ação
            embed = discord.Embed(
                title="Usuário Adicionado à Blacklist",
                description=f"**Usuário:** <@{user_id}> (`{user_id}`)\n"
                f"**Moderador:** {interaction.user.mention}\n"
                f"**Motivo:** {self.reason_input.value}",
                color=discord.Color.red(),
            )
            await log_action(
                bot=interaction.client,
                db=db,
                guild_id=interaction.guild.id,
                log_type="general",
                embed=embed,
            )

            await interaction.response.send_message(
                f"Usuário {user_id} adicionado à blacklist.", ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "ID de usuário inválido.", ephemeral=True
            )


class RemoveBlacklistModal(discord.ui.Modal, title="Remover Usuário da Blacklist"):
    user_id_input = discord.ui.TextInput(
        label="ID do Usuário",
        placeholder="Cole o ID do usuário do Discord para remover...",
        style=discord.TextStyle.short,
    )

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        try:
            user_id = int(self.user_id_input.value)
            db_user = db.query(User).filter(User.discord_id == user_id).first()
            if db_user:
                blacklist_entry = (
                    db.query(Blacklist).filter(Blacklist.user_id == db_user.id).first()
                )
                if blacklist_entry:
                    db.delete(blacklist_entry)
                    db.commit()

                    # Log da ação
                    embed = discord.Embed(
                        title="Usuário Removido da Blacklist",
                        description=f"**Usuário:** <@{user_id}> (`{user_id}`)\n"
                        f"**Moderador:** {interaction.user.mention}",
                        color=discord.Color.green(),
                    )
                    await log_action(
                        bot=interaction.client,
                        db=db,
                        guild_id=interaction.guild.id,
                        log_type="general",
                        embed=embed,
                    )

                    await interaction.response.send_message(
                        f"Usuário {user_id} removido da blacklist.", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "Usuário não encontrado na blacklist.", ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "Usuário não encontrado.", ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "ID de usuário inválido.", ephemeral=True
            )


class BlacklistView(discord.ui.View):
    def __init__(self, moderator: discord.User):
        super().__init__(timeout=None)
        self.moderator = moderator

    @discord.ui.button(
        label="Adicionar", style=discord.ButtonStyle.danger, custom_id="add_blacklist"
    )
    async def add_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = BlacklistModal(moderator=self.moderator)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Remover",
        style=discord.ButtonStyle.secondary,
        custom_id="remove_blacklist",
    )
    async def remove_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = RemoveBlacklistModal()
        await interaction.response.send_modal(modal)


class BlacklistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="black", description="Gerencia a blacklist de usuários.")
    @db_session_decorator
    async def black(self, interaction: discord.Interaction, db: Session):
        """
        Exibe o painel de gerenciamento da blacklist.
        """
        guild_config = (
            db.query(GuildConfig)
            .filter(GuildConfig.guild_id == interaction.guild.id)
            .first()
        )

        if (
            not guild_config
            or not (
                guild_config.analyst_role_id in [r.id for r in interaction.user.roles]
                or guild_config.mediator_role_id
                in [r.id for r in interaction.user.roles]
            )
        ):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Painel da Blacklist",
            description="Use os botões para adicionar ou remover usuários da blacklist.",
            color=discord.Color.dark_red(),
        )
        view = BlacklistView(moderator=interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(BlacklistCog(bot))

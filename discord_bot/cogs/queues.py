# discord_bot/cogs/queues.py

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import GuildConfig, Price, EmbedConfig, Queue
from ..views.queue_view import QueueView
from ..utils.modal_db_decorator import modal_db_session_decorator


class QueueModal(discord.ui.Modal, title="Criar Filas"):
    category_id_input = discord.ui.TextInput(
        label="ID da Categoria",
        placeholder="Cole o ID da categoria onde as filas serão criadas...",
        style=discord.TextStyle.short,
    )

    def __init__(self, queue_type: str, bot: commands.Bot):
        super().__init__()
        self.queue_type = queue_type
        self.bot = bot

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        category_id = int(self.category_id_input.value)
        category = interaction.guild.get_channel(category_id)

        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "ID de categoria inválido.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        queue_channels = ["1v1", "2v2", "3v3", "4v4"]
        for channel_name_suffix in queue_channels:
            queue_type = f"{self.queue_type}-{channel_name_suffix}"
            channel = await category.create_text_channel(name=queue_type)

            embed = discord.Embed(
                title=f"Fila para {queue_type}",
                description="Clique em um dos botões para entrar na fila.",
                color=discord.Color.dark_purple(),
            )
            message = await channel.send(
                embed=embed, view=QueueView(self.bot, queue_type)
            )

            # Criar a fila no banco de dados
            new_queue = Queue(
                channel_id=channel.id,
                message_id=message.id,
                queue_type=queue_type,
            )
            db.add(new_queue)
        db.commit()
        await interaction.followup.send(
            "Filas criadas com sucesso!", ephemeral=True
        )


class QueueSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Mobile", value="Mobile"),
            discord.SelectOption(label="Emulador", value="Emulador"),
            discord.SelectOption(label="Tático", value="Tático"),
            discord.SelectOption(label="Misto", value="Misto"),
        ]
        super().__init__(
            placeholder="Selecione a modalidade da fila...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        modal = QueueModal(queue_type=self.values[0], bot=self.bot)
        await interaction.response.send_modal(modal)


class QueuesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="filas", description="Cria as filas de partidas.")
    @app_commands.checks.has_permissions(administrator=True)
    async def queues(self, interaction: discord.Interaction):
        """
        Exibe um painel para criar as filas de partidas.
        """
        view = discord.ui.View()
        view.add_item(QueueSelect(bot=self.bot))
        await interaction.response.send_message(
            "Selecione a modalidade para criar as filas:", view=view, ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(QueuesCog(bot))

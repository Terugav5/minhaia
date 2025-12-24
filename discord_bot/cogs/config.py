# discord_bot/cogs/config.py

import discord
from discord import app_commands
from discord.ext import commands
from ..database.database import get_db
from ..database.models import GuildConfig
from sqlalchemy.orm import Session
from ..views.config_view import ConfigView


class ConfigCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="config", description="Painel de configuração do bot.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        """
        Exibe o painel de configuração do bot.
        Este comando só pode ser usado por administradores.
        """
        view = ConfigView(guild_id=interaction.guild.id)
        embed = discord.Embed(
            title="Painel de Configuração",
            description="Use os botões abaixo para configurar o bot.",
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCog(bot))

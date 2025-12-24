# discord_bot/cogs/id.py

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import GuildConfig
from ..utils.db_session import db_session_decorator


class CopyButton(discord.ui.Button):
    def __init__(self, text_to_copy: str):
        super().__init__(label="Copiar", style=discord.ButtonStyle.secondary)
        self.text_to_copy = text_to_copy

    async def callback(self, interaction: discord.Interaction):
        # Esta é uma interação fantasma, a cópia real é feita pelo cliente do Discord
        # com base no `custom_id` implícito ou outro mecanismo.
        # Para uma melhor UX, podemos informar o usuário.
        await interaction.response.send_message(
            f"ID e Senha para cópia:\n```{self.text_to_copy}```", ephemeral=True
        )


class IdCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="id", description="Envia as informações da sala para os jogadores."
    )
    @app_commands.describe(sala="O ID da sala.", senha="A senha da sala.")
    @db_session_decorator
    async def id(
        self, interaction: discord.Interaction, sala: str, senha: str, db: Session
    ):
        """
        Envia uma embed com o ID e a senha da sala, incluindo um botão para copiar.
        """
        # --- Verificação de Permissão ---
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

        # --- Criação da Embed ---
        embed = discord.Embed(
            title="Informações da Sala",
            description="A sala da partida foi criada. Boa sorte a todos!",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Sala (ID)", value=f"`{sala}`", inline=True)
        embed.add_field(name="Senha", value=f"`{senha}`", inline=True)
        embed.set_footer(text=f"Enviado por: {interaction.user.display_name}")

        # --- Criação da View com o Botão ---
        text_to_copy = f"ID: {sala}\nSenha: {senha}"
        view = discord.ui.View()
        # O Discord não tem um botão de "copiar" nativo.
        # A melhor abordagem é enviar o texto de forma que facilite a cópia.
        # Este botão apenas mostrará o texto novamente de forma efêmera.
        view.add_item(CopyButton(text_to_copy))

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(IdCog(bot))

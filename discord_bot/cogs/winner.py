# discord_bot/cogs/winner.py

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, GuildConfig
from utils.db_session import db_session_decorator


class WinnerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="vencedor", description="Declara o vencedor e o perdedor de uma partida."
    )
    @app_commands.describe(
        vencedor="O membro que venceu a partida.",
        perdedor="O membro que perdeu a partida.",
    )
    @db_session_decorator
    async def vencedor(
        self,
        interaction: discord.Interaction,
        vencedor: discord.Member,
        perdedor: discord.Member,
        db: Session,
    ):
        """
        Registra o resultado de uma partida, atualizando as estatísticas dos jogadores.
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

        # --- Evitar que o vencedor e o perdedor sejam a mesma pessoa ---
        if vencedor.id == perdedor.id:
            await interaction.response.send_message(
                "O vencedor e o perdedor não podem ser a mesma pessoa.",
                ephemeral=True,
            )
            return

        # --- Atualizar Vencedor ---
        db_vencedor = (
            db.query(User).filter(User.discord_id == vencedor.id).first()
        )
        if not db_vencedor:
            db_vencedor = User(discord_id=vencedor.id, wins=1, coins=1, losses=0)
            db.add(db_vencedor)
        else:
            db_vencedor.wins += 1
            db_vencedor.coins += 1

        # --- Atualizar Perdedor ---
        db_perdedor = (
            db.query(User).filter(User.discord_id == perdedor.id).first()
        )
        if not db_perdedor:
            db_perdedor = User(discord_id=perdedor.id, losses=1, wins=0, coins=0)
            db.add(db_perdedor)
        else:
            db_perdedor.losses += 1

        db.commit()

        # --- Mensagem de Confirmação ---
        embed = discord.Embed(
            title="Resultado da Partida Registrado",
            description=f"**Vencedor:** {vencedor.mention}\n**Perdedor:** {perdedor.mention}",
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Registrado por: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @vencedor.error
    async def vencedor_error(self, interaction: discord.Interaction, error):
        """Trata erros para o comando /vencedor."""
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Ocorreu um erro ao registrar o resultado da partida.", ephemeral=True
            )
            print(f"Erro no comando /vencedor: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(WinnerCog(bot))

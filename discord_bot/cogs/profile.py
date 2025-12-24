# discord_bot/cogs/profile.py

import discord
from discord.ext import commands
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User
from utils.db_session import db_session_decorator


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="p", help="Exibe o perfil de um usuário.")
    @db_session_decorator
    async def profile(
        self, ctx: commands.Context, member: discord.Member = None, db: Session = None
    ):
        """
        Exibe o perfil de um usuário com suas estatísticas.
        Uso: .p @usuario
        Se nenhum usuário for mencionado, exibe o perfil do autor do comando.
        """
        # Se nenhum membro for mencionado, o alvo é o autor da mensagem
        target_user = member or ctx.author

        # Busca o usuário no banco de dados
        db_user = db.query(User).filter(User.discord_id == target_user.id).first()

        if not db_user:
            # Se o usuário não estiver no banco, exibe um perfil padrão
            wins = 0
            losses = 0
            coins = 0
        else:
            wins = db_user.wins
            losses = db_user.losses
            coins = db_user.coins

        # Cria a embed com as informações do perfil
            embed = discord.Embed(
                title=f"Perfil de {target_user.display_name}",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
            embed.add_field(name="🏆 Vitórias", value=f"`{wins}`", inline=True)
            embed.add_field(name="💀 Derrotas", value=f"`{losses}`", inline=True)
            embed.add_field(name="💰 Coins", value=f"`{coins}`", inline=True)

            # Calcula o K/D (Kills/Deaths) ou W/L (Wins/Losses)
            # Evita divisão por zero
            if losses > 0:
                win_rate = (wins / (wins + losses)) * 100
                embed.add_field(name="📊 Win Rate", value=f"`{win_rate:.2f}%`", inline=False)
            else:
                embed.add_field(name="📊 Win Rate", value="`N/A`", inline=False)

            await ctx.send(embed=embed)

    @profile.error
    async def profile_error(self, ctx, error):
        """Trata erros para o comando de perfil."""
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Não consegui encontrar esse membro. Por favor, mencione um usuário válido.")
        else:
            await ctx.send("Ocorreu um erro ao buscar o perfil.")
            print(f"Erro no comando .p: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))

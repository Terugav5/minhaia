# main.py (Raiz do Projeto)

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord_bot.database.database import create_tables

# --- Carregamento das Variáveis de Ambiente ---
# Carrega as variáveis do arquivo .env para o ambiente de execução.
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- Configuração dos Intents ---
# Define os eventos que o bot irá receber do Discord.
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# --- Inicialização do Bot ---
# Instancia o bot com prefixo de comando e intents.
bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    """
    Evento acionado quando o bot está online e pronto.
    """
    print(f"Bot conectado como {bot.user}")
    print("------")
    # Sincroniza os comandos de barra (slash commands) com o Discord.
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


async def load_cogs():
    """
    Carrega todas as extensões (cogs) da pasta 'discord_bot/cogs'.
    """
    # Constrói o caminho para a pasta de cogs a partir da raiz do projeto.
    cogs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "discord_bot", "cogs")
    for filename in os.listdir(cogs_path):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                # O caminho para a extensão (ex: discord_bot.cogs.config) permanece o mesmo.
                await bot.load_extension(f"discord_bot.cogs.{filename[:-3]}")
                print(f"Cog '{filename[:-3]}' carregado com sucesso.")
            except Exception as e:
                print(f"Erro ao carregar o cog '{filename[:-3]}': {e}")


async def main():
    """
    Função principal que inicializa o bot.
    """
    print("Criando tabelas no banco de dados...")
    create_tables()
    print("Tabelas criadas com sucesso.")

    # Carrega os cogs antes de iniciar o bot.
    await load_cogs()

    # Inicia a conexão do bot com o Discord.
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    # Executa a função principal no loop de eventos do asyncio.
    asyncio.run(main())

# discord_bot/main.py

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database.database import create_tables

# --- Carregamento das Variáveis de Ambiente ---
# Carrega as variáveis do arquivo .env para o ambiente de execução.
# É uma boa prática para manter informações sensíveis, como tokens, fora do código.
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- Configuração dos Intents ---
# Intents definem quais eventos o seu bot irá receber do Discord.
# É importante solicitar apenas os intents que seu bot realmente precisa.
intents = discord.Intents.default()
intents.members = True  # Necessário para acessar informações dos membros
intents.message_content = True  # Necessário para ler o conteúdo das mensagens

# --- Inicialização do Bot ---
# Criamos uma instância do bot, definindo o prefixo dos comandos e os intents.
# O prefixo '.' foi escolhido, mas o bot focará em comandos de barra (slash commands).
bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    """
    Evento que é acionado quando o bot está online e pronto para receber comandos.
    """
    print(f"Bot conectado como {bot.user}")
    print("------")
    # Sincroniza os comandos de barra com o Discord.
    # Isso garante que os comandos de barra apareçam para os usuários.
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


async def load_cogs():
    """
    Carrega todas as extensões (cogs) da pasta 'cogs'.
    Cogs ajudam a organizar os comandos em diferentes arquivos.
    """
    # Constrói o caminho para a pasta de cogs de forma robusta
    cogs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")
    # Itera sobre todos os arquivos na pasta 'cogs'
    for filename in os.listdir(cogs_path):
        # Verifica se o arquivo é um arquivo Python
        if filename.endswith(".py") and not filename.startswith("__"):
            # Carrega a extensão, usando o caminho 'discord_bot.cogs.nome_do_arquivo'
            try:
                await bot.load_extension(f"discord_bot.cogs.{filename[:-3]}")
                print(f"Cog '{filename[:-3]}' carregado com sucesso.")
            except Exception as e:
                print(f"Erro ao carregar o cog '{filename[:-3]}': {e}")


async def main():
    """
    Função principal que inicializa o bot.
    """
    # Cria as tabelas no banco de dados se elas ainda não existirem.
    print("Criando tabelas no banco de dados...")
    create_tables()
    print("Tabelas criadas com sucesso.")

    # Carrega os cogs.
    await load_cogs()

    # Inicia o bot.
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio

    # Executa a função main no loop de eventos do asyncio.
    asyncio.run(main())

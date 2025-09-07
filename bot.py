import discord
from discord.ext import commands
import asyncio
import os

# Caminho do token
TOKEN_PATH = "token/token.txt"

# Intents necessários
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Lista de cogs (comandos)
COGS = [
    "comandos.ping",
    "comandos.alianca",
    "comandos.rank"
]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[OK] Comando carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Não foi possível carregar {cog}: {e}")

@bot.event
async def on_ready():
    print(f":robot: Bot online como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f":white_check_mark: {len(synced)} comandos de barra sincronizados:")
        for cmd in synced:
            print(f"  - {cmd.name}: {cmd.description}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

async def main():
    async with bot:
        await load_cogs()
        # Lê o token do arquivo
        if not os.path.exists(TOKEN_PATH):
            print(f"[ERRO] Token não encontrado em {TOKEN_PATH}")
            return
        with open(TOKEN_PATH, "r") as f:
            token = f.read().strip()
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
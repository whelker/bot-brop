import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

class Vincular(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command
    @app_commands.command(name="vincular", description="Vincule seu nick do WPlace ao seu perfil")
    async def vincular(self, interaction: discord.Interaction, nick: str):
        # Validação do formato do nick
        if "#" not in nick:
            await interaction.response.send_message(
                "<:emoji_14:1415786173535621250> **Formato inválido! Use: Nick#1234**",
                ephemeral=True
            )
            return

        # Conecta ao banco de dados
        conn = sqlite3.connect("players.db")
        c = conn.cursor()

        # Insere ou atualiza o usuário
        c.execute("""
            INSERT INTO users(discord_id, wplace_nick)
            VALUES(?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET wplace_nick=excluded.wplace_nick
        """, (str(interaction.user.id), nick))

        conn.commit()
        conn.close()

        # Resposta visível apenas para o usuário
        await interaction.response.send_message(
            f"<a:emoji_13:1415782124254138378> Seu nick **{nick}** foi vinculado com sucesso ao seu perfil!",
            ephemeral=True
        )

# Função para adicionar a cog
async def setup(bot: commands.Bot):
    await bot.add_cog(Vincular(bot))
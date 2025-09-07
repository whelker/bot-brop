import discord
from discord import app_commands
from discord.ext import commands
import time

class Ping(commands.Cog):
    def _init_(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Mostra sua latência")
    async def ping(self, interaction: discord.Interaction):
        # Calcula o ping do usuário
        start_time = time.time()
        await interaction.response.defer(thinking=True)
        end_time = time.time()
        user_ping = round((end_time - start_time) * 1000)

        # Ping do bot
        bot_ping = round(self.bot.latency * 1000)

        # Avaliação da latência e escolha da thumbnail
        if user_ping <= 50:
            status = "*Excelente* 🟢"
            thumb_url = "https://cdn.discordapp.com/attachments/1409248231463981159/1409258282748481697/2_Sem_Titulo_20250824152733.png"
            color = discord.Color.green()
        elif user_ping <= 150:
            status = "*Boa* 🟡"
            thumb_url = "https://cdn.discordapp.com/attachments/1409248231463981159/1409258372536205354/2_Sem_Titulo_20250824152800.png"
            color = discord.Color.gold()
        else:
            status = "*Péssima* 🔴"
            thumb_url = "https://cdn.discordapp.com/attachments/1409248231463981159/1409258422242771148/2_Sem_Titulo_20250824152831.png"
            color = discord.Color.red()

        # Cria a embed
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"• Sua latência é de *{user_ping}ms\n• Minha latência é de *{bot_ping}ms*\n\n<:emoji_3:1409635043864870962> Sua latência está {status}!*",
            color=color
        )
        embed.set_thumbnail(url=thumb_url)
        embed.set_footer(
            text="Feito por !ﾠshotz",
            icon_url="https://cdn.discordapp.com/attachments/1409248231463981159/1409249440220577832/1756061531120.png"
        )

        # Envia a embed
        await interaction.followup.send(embed=embed)

# Setup do cog
async def setup(bot):
    await bot.add_cog(Ping(bot))
import discord
from discord import app_commands
from discord.ext import commands

class InfoCalc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="infocalc", description="Exibe tutorial detalhado de uso do comando /calc.")
    async def infocalc(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🧮 Tutorial: Como usar o comando /calc",
            color=0x2d7ff9,
            description=(
                "Este comando calcula novas coordenadas de deslocamento de pixels a partir de coordenadas copiadas do site.\n\n"
                "**Parâmetros:**\n"
                "• `coordenadas`: Cole exatamente como copiado do site, ex: (Tl X: 723, Tl Y: 1084, Px X: 539, Px Y: 662)\n"
                "• `Direção 1`: Primeiro deslocamento. Ex: c10, d30, b5, e2\n"
                "• `Direção 2`: Segundo deslocamento (opcional). Ex: d20\n\n"
                "**Como indicar direções:**\n"
                ":arrow_up: `c` = Para cima\n"
                ":arrow_down: `b` = Para baixo\n"
                ":arrow_left: `e` = Para esquerda\n"
                ":arrow_right: `d` = Para direita\n\n"
                "**Exemplo de uso:**\n"
                "/calc coordenadas: (Tl X: 723, Tl Y: 1084, Px X: 539, Px Y: 662) c10 d30\n\n"
                "Você pode usar apenas um deslocamento, ou dois, na ordem desejada. Cada deslocamento é aplicado sequencialmente."
            )
        )
        embed.add_field(
            name="Dicas",
            value="- Sempre cole as coordenadas entre parênteses.\n- Os deslocamentos devem ser informados como letra da direção + número de pixels.",
            inline=False
        )
        embed.set_footer(text="Qualquer dúvida, use este comando novamente!\nDeveloped by @euleozin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(InfoCalc(bot))

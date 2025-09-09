import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

THUMBNAIL = "https://cdn.discordapp.com/attachments/1409248231463981159/1410103092703395850/1756265132713.png"
FOOTER_ICON = "https://cdn.discordapp.com/attachments/1409248231463981159/1414731583218520145/5825a5d4609bac3459e976fa6b26a7a3.png"

BROP_NAME = "BROP Enterprises"

API_ENDPOINTS = {
    "alliance": {
        "Hoje": "https://backend.wplace.live/leaderboard/alliance/today",
        "Semana": "https://backend.wplace.live/leaderboard/alliance/week",
        "Mês": "https://backend.wplace.live/leaderboard/alliance/month",
        "Geral": "https://backend.wplace.live/leaderboard/alliance/all-time",
    },
    "region": {
        "Hoje": "https://backend.wplace.live/leaderboard/region/today/0",
        "Semana": "https://backend.wplace.live/leaderboard/region/week/0",
        "Mês": "https://backend.wplace.live/leaderboard/region/month/0",
        "Geral": "https://backend.wplace.live/leaderboard/region/all-time/0",
    },
    "country": {
        "Hoje": "https://backend.wplace.live/leaderboard/country/today",
        "Semana": "https://backend.wplace.live/leaderboard/country/week",
        "Mês": "https://backend.wplace.live/leaderboard/country/month",
        "Geral": "https://backend.wplace.live/leaderboard/country/all-time",
    },
    "player": {
        "Hoje": "https://backend.wplace.live/leaderboard/player/today",
        "Semana": "https://backend.wplace.live/leaderboard/player/week",
        "Mês": "https://backend.wplace.live/leaderboard/player/month",
        "Geral": "https://backend.wplace.live/leaderboard/player/all-time",
    },
}


class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_data(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://wplace.live",
            "Referer": "https://wplace.live/",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Erro {resp.status} ao buscar dados.")
                return await resp.json()

    def format_rank_page(self, data, page: int, rank_type: str, periodo: str):
        start = page * 10
        end = start + 10
        page_data = data[start:end]

        desc = ""
        for i, entry in enumerate(page_data, start=start + 1):
            name = entry.get("name", "?")
            pixels = entry.get("pixelsPainted", entry.get("pixels", 0))

            if rank_type == "alliance" and name.lower() == BROP_NAME.lower():
                name = f"🇧🇷 {BROP_NAME} 🇧🇷"

            medal = ""
            if i == 1:
                medal = "<:emoji_4:1410092029207380058> "
            elif i == 2:
                medal = "<:emoji_6:1410092846500810862> "
            elif i == 3:
                medal = "<:emoji_6:1410092631844978853> "

            desc += f"{medal}{i}. {name} — {pixels:,} pixels\n"

        embed = discord.Embed(
            title=f"<:emoji_2:1409634610828017755> Rank {rank_type.capitalize()} — {periodo}",
            description=desc or "Nenhum dado encontrado.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=THUMBNAIL)
        embed.set_footer(text="Feito por !  zenitsu", icon_url=FOOTER_ICON)

        if rank_type == "alliance":
            brop = next((a for a in data if a["name"].lower() == BROP_NAME.lower()), None)
            if brop:
                pos = data.index(brop) + 1
                embed.add_field(
                    name="<:emoji_10:1410249964227006618> Destaques",
                    value=f"<:emoji_11:1410250212018098216> 🇧🇷 {BROP_NAME} 🇧🇷 — Posição {pos} — {brop['pixelsPainted']:,} pixels",
                    inline=False
                )
            else:
                embed.add_field(
                    name="<:emoji_10:1410249964227006618> Destaques",
                    value=f"Não foi possível localizar {BROP_NAME}",
                    inline=False
                )

        return embed

    async def send_rank(self, interaction: discord.Interaction, rank_type: str, periodo: str):
        url = API_ENDPOINTS[rank_type][periodo]
        try:
            data = await self.fetch_data(url)
        except Exception as e:
            await interaction.response.edit_message(content=f"⚠️ Erro interno ao buscar o rank: `{e}`")
            return

        max_pages = 5
        page = 0
        embed_rank = self.format_rank_page(data, page, rank_type, periodo)

        buttons = discord.ui.View()

        async def prev_callback(ip: discord.Interaction):
            if ip.user.id != interaction.user.id:
                await ip.response.send_message("❌ Apenas quem enviou o comando pode usar estes botões.", ephemeral=True)
                return
            nonlocal page, embed_rank
            page = page - 1 if page > 0 else max_pages - 1
            embed_rank = self.format_rank_page(data, page, rank_type, periodo)
            await ip.response.edit_message(embed=embed_rank, view=buttons)

        async def next_callback(ip: discord.Interaction):
            if ip.user.id != interaction.user.id:
                await ip.response.send_message("❌ Apenas quem enviou o comando pode usar estes botões.", ephemeral=True)
                return
            nonlocal page, embed_rank
            page = page + 1 if page < max_pages - 1 else 0
            embed_rank = self.format_rank_page(data, page, rank_type, periodo)
            await ip.response.edit_message(embed=embed_rank, view=buttons)

        async def back_callback(ip: discord.Interaction):
            if ip.user.id != interaction.user.id:
                await ip.response.send_message("❌ Apenas quem enviou o comando pode usar este botão.", ephemeral=True)
                return
            await self.open_period_menu(ip, rank_type)

        prev_button = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.secondary)
        next_button = discord.ui.Button(label="➡️", style=discord.ButtonStyle.secondary)
        back_button = discord.ui.Button(label="Voltar", style=discord.ButtonStyle.danger)

        prev_button.callback = prev_callback
        next_button.callback = next_callback
        back_button.callback = back_callback

        buttons.add_item(prev_button)
        buttons.add_item(next_button)
        buttons.add_item(back_button)

        await interaction.response.edit_message(embed=embed_rank, view=buttons)

    async def open_period_menu(self, interaction: discord.Interaction, rank_type: str):
        embed2 = discord.Embed(
            title=f"<:emoji_2:1409634610828017755> Rank {rank_type.capitalize()}",
            description="<:emoji_8:1410099355356102726> Qual período deseja selecionar?",
            color=discord.Color.green()
        )
        embed2.set_thumbnail(url=THUMBNAIL)
        embed2.set_footer(text="Feito por !  zenitsu", icon_url=FOOTER_ICON)

        view2 = discord.ui.View()

        for periodo in ["Hoje", "Semana", "Mês", "Geral"]:
            btn = discord.ui.Button(label=periodo, style=discord.ButtonStyle.success)

            async def callback(i2: discord.Interaction, p=periodo):
                await self.send_rank(i2, rank_type, p)

            btn.callback = callback
            view2.add_item(btn)

        async def back_callback(i: discord.Interaction):
            if i.user.id != interaction.user.id:
                await i.response.send_message("❌ Apenas quem enviou o comando pode usar este botão.", ephemeral=True)
                return
            await self.rank(i)

        back_button = discord.ui.Button(label="Voltar", style=discord.ButtonStyle.danger)
        back_button.callback = back_callback
        view2.add_item(back_button)

        await interaction.response.edit_message(embed=embed2, view=view2)

    @app_commands.command(name="rank", description="Mostra os ranks do wplace")
    async def rank(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<:emoji_2:1409634610828017755> Rank wplace",
            description="<:emoji_7:1410098645008912506> Qual Rank você deseja selecionar?",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=THUMBNAIL)
        embed.set_footer(text="Feito por !  zenitsu", icon_url=FOOTER_ICON)

        view = discord.ui.View()

        for rtype, label in [("region", "Regiões"), ("country", "Países"),
                             ("player", "Jogadores"), ("alliance", "Aliança")]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.success)

            async def callback(i: discord.Interaction, rt=rtype):
                await self.open_period_menu(i, rt)

            btn.callback = callback
            view.add_item(btn)


        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Rank(bot))
import os, json, aiohttp, discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

BROP_NAME = "BROP Enterprises"

THUMBNAIL = "https://cdn.discordapp.com/attachments/1409248231463981159/1410103092703395850/1756265132713.png?ex=68c04717&is=68bef597&hm=176b622874f99dbedc483e21e60c0a733742fc04897883f12e5522ca0147a127"
FOOTER_ICON = "https://cdn.discordapp.com/attachments/1409248231463981159/1414731583218520145/5825a5d4609bac3459e976fa6b26a7a3.png?ex=68c0a2f5&is=68bf5175&hm=25adcd600f59da3ea9c4d1a4c9729403b84bd7529a941c7a89c463f3e836d222"


RECORD_FILE = "brop_records.json"


PERIODS = {
    "Diário":  ("daily",  "https://backend.wplace.live/leaderboard/alliance/today"),
    "Semanal": ("weekly", "https://backend.wplace.live/leaderboard/alliance/week"),
    "Mensal":  ("monthly","https://backend.wplace.live/leaderboard/alliance/month"),
}

def _ensure_record_file():
    if not os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "daily": {"pixels": 0, "date": None},
                "weekly": {"pixels": 0, "date": None},
                "monthly": {"pixels": 0, "date": None}
            }, f, ensure_ascii=False, indent=2)

def load_records():
    _ensure_record_file()
    with open(RECORD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_records(data: dict):
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class RecordeBROP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def fetch_brop_pixels(self, url: str) -> int:
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
                data = await resp.json()


        for a in data:
            name = a.get("name", "")
            if isinstance(name, str) and name.lower() == BROP_NAME.lower():
                return a.get("pixelsPainted", a.get("pixels", 0))
        return 0


    def initial_embed(self) -> discord.Embed:
        e = discord.Embed(
            title="👑 Recorde de pixels colocados",
            description="<:emoji_8:1410099355356102726> Qual período deseja selecionar para ver o recorde de pixels pintados?",
            color=discord.Color.green()
        )
        e.set_thumbnail(url=THUMBNAIL)
        e.set_footer(text="Feito por !  zenitsu", icon_url=FOOTER_ICON)
        return e

    def result_embed(self, periodo_label: str, atual: int, record: dict, novo: bool) -> discord.Embed:
        data_str = record["date"] if record["date"] else "—"
        e = discord.Embed(
            title=f"<:emoji_7:1410098645008912506> Recorde {periodo_label}",
            description=(
                f"<:emoji_1:1409634573813415998> • Pixels atuais da <:emoji_11:1410250212018098216> {BROP_NAME}: **{atual:,}**\n\n"
                f"<:emoji_2:1409634610828017755> • Recorde: **{record['pixels']:,}**\n"
                f"📅 • Data do recorde: {data_str}"
            ),
            color=discord.Color.green()
        )
        e.set_thumbnail(url=THUMBNAIL)
        e.set_footer(text="Feito por !  zenitsu", icon_url=FOOTER_ICON)
        return e


    def make_back_view(self, owner_id: int, initial_view: discord.ui.View):
        view = discord.ui.View()
        back_btn = discord.ui.Button(label="Voltar", style=discord.ButtonStyle.danger)

        async def back_cb(i: discord.Interaction):
            if i.user.id != owner_id:
                await i.response.send_message("❌ Apenas quem executou o comando pode usar este botão.", ephemeral=True)
                return
            await i.response.edit_message(embed=self.initial_embed(), view=initial_view)

        back_btn.callback = back_cb
        view.add_item(back_btn)
        return view


    @app_commands.command(name="recordes", description="Recorde de pixels colocados da BROP Enterprises")
    async def recorde(self, interaction: discord.Interaction):
        owner_id = interaction.user.id
        initial_view = discord.ui.View()


        for label in ("Diário", "Semanal", "Mensal"):
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.success)

            async def cb(i: discord.Interaction, p=label):
                if i.user.id != owner_id:
                    await i.response.send_message("❌ Apenas quem executou o comando pode usar estes botões.", ephemeral=True)
                    return

                key, url = PERIODS[p]
                try:
                    atual = await self.fetch_brop_pixels(url)
                except Exception as e:
                    await i.response.send_message(f"⚠️ Erro ao buscar dados: `{e}`", ephemeral=True)
                    return

                records = load_records()
                best = records[key]
                if atual > best["pixels"]:
                    records[key]["pixels"] = atual
                    records[key]["date"] = datetime.utcnow().strftime("%d/%m/%Y")
                    save_records(records)
                    best = records[key]

                back_view = self.make_back_view(owner_id, initial_view)
                await i.response.edit_message(embed=self.result_embed(p, atual, best, False), view=back_view)

            btn.callback = cb
            initial_view.add_item(btn)


        await interaction.response.send_message(embed=self.initial_embed(), view=initial_view)

async def setup(bot):
    await bot.add_cog(RecordeBROP(bot))
import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp, io
from PIL import Image
from datetime import datetime


BOT_OWNER_ID = 917768381896212530

CHUNKS = [
    (720,1085), (721,1085), (722,1085),   # Linha 1
    (720,1084), (721,1084), (722,1084),   # Linha 2
    (720,1083), (721,1083), (722,1083),   # Linha 3
    (720,1082), (721,1082), (722,1082)    # Linha 4
]

BASE_URL = "https://backend.wplace.live/files/s0/tiles/{x}/{y}.png"
TILE_SIZE = 1000

class Manitorar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitor_interval = 3600
        self.target_channel_id = None
        self.monitor_loop.change_interval(seconds=self.monitor_interval)

    async def fetch_chunk(self, session, x, y):
        url = BASE_URL.format(x=x, y=y)
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
        except:
            return None
        return None

    async def build_map(self, chunks):
        async with aiohttp.ClientSession() as session:
            images = {}
            for x, y in chunks:
                img = await self.fetch_chunk(session, x, y)
                if img:
                    images[(x, y)] = img

        xs = [c[0] for c in chunks]
        ys = [c[1] for c in chunks]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        width = (max_x - min_x + 1) * TILE_SIZE
        height = (max_y - min_y + 1) * TILE_SIZE

        result = Image.new("RGBA", (width, height), (255, 255, 255, 255))

        for (x, y), img in images.items():
            px = (x - min_x) * TILE_SIZE
            py = (y - min_y) * TILE_SIZE
            result.paste(img, (px, py), img)

        return result

    @tasks.loop(seconds=3600)
    async def monitor_loop(self):
        if not self.target_channel_id:
            return
        channel = self.bot.get_channel(self.target_channel_id)
        if not channel:
            return

        img = await self.build_map(CHUNKS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        agora = datetime.now().strftime("%d/%m %H:%M")

        embed = discord.Embed(
            title=f"<:emoji_12:1415038636604526642> Atualização diária — {agora}",
            description="",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://monitor.png")
        embed.set_footer(
            text="Feito por !  zenitsu",
            icon_url="https://cdn.discordapp.com/attachments/1409248231463981159/1414731583218520145/5825a5d4609bac3459e976fa6b26a7a3.png?ex=68c14bb5&is=68bffa35&hm=22c4e189bb1ed952d92c822360b873d71f277fff0332304629d8aff7ee2fb8e3"
        )

        file = discord.File(buf, "monitor.png")
        await channel.send(embed=embed, file=file)

    @commands.Cog.listener()
    async def on_ready(self):
        print("🔄 Cog Manitorar carregado.")

    @app_commands.command(
        name="manitorar",
        description="Liga ou desliga o monitoramento da arte azul da bandeira do Brasil"
    )
    @app_commands.describe(
        status="Ativar ou desativar o monitoramento",
        tempo="Número do intervalo (ex: 1, 2, 3)",
        unidade="Unidade de tempo: minutos, horas ou dias",
        canal="Canal onde será enviado o monitoramento"
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(name="On", value="on"),
            app_commands.Choice(name="Off", value="off"),
        ],
        unidade=[
            app_commands.Choice(name="Minutos", value="minutos"),
            app_commands.Choice(name="Horas", value="horas"),
            app_commands.Choice(name="Dias", value="dias"),
        ]
    )
    async def manitorar(
        self,
        interaction: discord.Interaction,
        status: str,
        tempo: int = 1,
        unidade: str = "horas",
        canal: discord.TextChannel = None
    ):

        if not interaction.user.guild_permissions.administrator and interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message(
                "🚫 Você não tem permissão para usar este comando.",
                ephemeral=True
            )
            return

        if status == "off":
            self.monitor_loop.stop()
            await interaction.response.send_message(
                "❌ Monitoramento **desligado**.",
                ephemeral=True
            )
            return

        if canal:
            self.target_channel_id = canal.id
        else:
            self.target_channel_id = interaction.channel.id

        if unidade == "minutos":
            self.monitor_interval = tempo * 60
        elif unidade == "horas":
            self.monitor_interval = tempo * 3600
        elif unidade == "dias":
            self.monitor_interval = tempo * 86400

        self.monitor_loop.change_interval(seconds=self.monitor_interval)

        if not self.monitor_loop.is_running():
            self.monitor_loop.start()

        await interaction.response.send_message(
            f"✅ Monitoramento **ativado** a cada {tempo} {unidade} no canal "
            f"{canal.mention if canal else interaction.channel.mention}.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Manitorar(bot))
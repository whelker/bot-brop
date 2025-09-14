import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp, io
import asyncio
from PIL import Image
from datetime import datetime
from pathlib import Path
import imageio
folder = Path("monitoramento_imgs")


BOT_OWNER_ID = 917768381896212530

CHUNKS = [
    (719, 1081), (720, 1081), (721, 1081), (722, 1081), (723, 1081),
    (719, 1082), (720, 1082), (721, 1082), (722, 1082), (723, 1082),
    (719, 1083), (720, 1083), (721, 1083), (722, 1083), (723, 1083),
    (719, 1084), (720, 1084), (721, 1084), (722, 1084), (723, 1084),
    (719, 1085), (720, 1085), (721, 1085), (722, 1085), (723, 1085),
    (719, 1086), (720, 1086), (721, 1086), (722, 1086), (723, 1086)
]

BASE_URL = "https://backend.wplace.live/files/s0/tiles/{x}/{y}.png"
TILE_SIZE = 1000

class Manitorar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gif_interval = 3600 
        self.target_channel_id = None
        self.monitor_loop.change_interval(seconds=900)
        self.gif_loop.change_interval(seconds=self.gif_interval)
        self.first_capture_ready = asyncio.Event()
        try:
            existing = list(Path("monitoramento_imgs").glob("monitor_*.png"))
            if existing:
                self.first_capture_ready.set()
        except Exception:
            pass
    def save_image_to_folder(self, img):
        folder = Path("monitoramento_imgs")
        folder.mkdir(exist_ok=True)
        try:
            ow, oh = img.size
            scale = 0.30
            nw, nh = max(1, int(ow * scale)), max(1, int(oh * scale))
            if (nw, nh) != (ow, oh):
                img = img.copy().resize((nw, nh), Image.LANCZOS)
                print(f"[MONITOR] Redimensionado de {(ow, oh)} para {(nw, nh)} (30%).")
        except Exception as e:
            print(f"[MONITOR][WARN] Falha ao redimensionar (30%): {e}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = folder / f"monitor_{timestamp}.png"
        img.save(path, format="PNG")
        return path

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

    @tasks.loop(seconds=900)
    async def monitor_loop(self):
        print("[MONITOR] Iniciando captura de imagem...")
        img = await self.build_map(CHUNKS)
        saved_path = self.save_image_to_folder(img)
        try:
            print(f"[MONITOR] Imagem capturada e salva em: {saved_path}")
        except Exception:
            print("[MONITOR] Imagem capturada e salva.")
        if not self.first_capture_ready.is_set():
            self.first_capture_ready.set()

    @tasks.loop(seconds=3600)
    async def gif_loop(self):
        if not self.first_capture_ready.is_set():
            await self.first_capture_ready.wait()
        print("[GIF] Início do loop de geração de GIF.")
        if not self.target_channel_id:
            print("[GIF] Nenhum canal alvo definido; saindo.")
            return
        channel = self.bot.get_channel(self.target_channel_id)
        if not channel:
            print(f"[GIF] Canal alvo {self.target_channel_id} não encontrado; saindo.")
            return
        folder = Path("monitoramento_imgs")
        files = sorted(folder.glob("monitor_*.png"))
        print(f"[GIF] {len(files)} imagens encontradas na pasta para GIF.")
        if len(files) >= 40:
            before = len(files)
            to_delete = files[:-1]
            for i, f in enumerate(to_delete):
                if i % 2 == 0:
                    f.unlink()
            files = sorted(folder.glob("monitor_*.png"))
            after = len(files)
            print(f"[GIF] Limpeza aplicada. Antes: {before} | Depois: {after}")

        if not files:
            print("[GIF] Nenhuma imagem disponível após limpeza; saindo.")
            return
        print(f"[GIF] Usando {len(files)} frames no tamanho original.")

        frames = []
        for f in files:
            try:
                im = Image.open(f).convert("RGB")
                frames.append(im)
            except Exception as e:
                print(f"[GIF][WARN] Frame ignorado por erro ao abrir {f}: {e}")

        if not frames:
            print("[GIF] Nenhum frame válido após processamento; saindo.")
            return

        gif_path = folder / "monitor.gif"
        print(f"[GIF] Gerando GIF em {gif_path} com {len(frames)} frames...")
        try:
            frames[0].save(
                str(gif_path),
                save_all=True,
                append_images=frames[1:],
                duration=250,
                loop=0,
                optimize=True,
            )
            print("[GIF] GIF gerado com sucesso.")
        except Exception as e:
            print(f"[GIF][ERRO] Falha ao salvar GIF: {e}")
            return

        agora = datetime.now().strftime("%d/%m %H:%M")
        # Anexa também a última imagem capturada
        try:
            latest_png = files[-1]
            gif_file = discord.File(gif_path, filename="monitor.gif")
            png_file = discord.File(str(latest_png), filename=latest_png.name)
            await channel.send(
                content=f"🎞️ GIF e Última captura do monitoramento — {agora}.",
                files=[gif_file, png_file]
            )
            print(f"[GIF] GIF e última imagem enviados com sucesso ao canal: {latest_png.name}")
        except Exception as e:
            print(f"[GIF][ERRO] Falha ao enviar GIF/PNG ao Discord: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        print("🔄 Cog Monitorar carregado.")

    @app_commands.command(
        name="attdiario",
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
            self.gif_loop.stop()
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

        self.gif_interval = self.monitor_interval 
        self.gif_loop.change_interval(seconds=self.gif_interval)
        if not self.monitor_loop.is_running():
            self.monitor_loop.start()

        await interaction.response.send_message(
            f"✅ Monitoramento **ativado** no canal "
            f"{canal.mention if canal else interaction.channel.mention}.",
            ephemeral=True
        )

        if not self.gif_loop.is_running():
            self.gif_loop.start()

async def setup(bot):
    await bot.add_cog(Manitorar(bot))
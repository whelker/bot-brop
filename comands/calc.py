import discord
from discord import app_commands
from discord.ext import commands
import re

TILE_SIZE = 1000
TILE_OFFSET_X = 0
TILE_OFFSET_Y = 0

def to_global(tileX, tileY, pixelX, pixelY):
    globalX = (tileX - TILE_OFFSET_X) * TILE_SIZE + pixelX
    globalY = (tileY - TILE_OFFSET_Y) * TILE_SIZE + pixelY
    return globalX, globalY

def apply_delta(globalX, globalY, deltaX, deltaY):
    return globalX + deltaX, globalY + deltaY

def clamp(x, y):
    clampedX = max(0, x)
    clampedY = max(0, y)
    clamped = clampedX != x or clampedY != y
    return clampedX, clampedY, clamped

def to_tile(globalX, globalY):
    tileX = globalX // TILE_SIZE + TILE_OFFSET_X
    tileY = globalY // TILE_SIZE + TILE_OFFSET_Y
    pixelX = ((globalX % TILE_SIZE) + TILE_SIZE) % TILE_SIZE
    pixelY = ((globalY % TILE_SIZE) + TILE_SIZE) % TILE_SIZE
    return tileX, tileY, pixelX, pixelY


def parse_coords(text):
    pattern = r'Tl X:\s*(\d+),\s*Tl Y:\s*(\d+),\s*Px X:\s*(\d+),\s*Px Y:\s*(\d+)'
    match = re.search(pattern, text)
    if not match:
        return None
    return tuple(map(int, match.groups()))

def parse_deltas(args):
    delta_map = {'c': (0, -1), 'b': (0, 1), 'e': (-1, 0), 'd': (1, 0)}
    dx = dy = 0
    for arg in args:
        m = re.match(r'([cbed])(\d+)', arg.lower())
        if m:
            dir_, val = m.group(1), int(m.group(2))
            if dir_ in ['d', 'e']:
                dx += delta_map[dir_][0] * val
            if dir_ in ['c', 'b']:
                dy += delta_map[dir_][1] * val
    dx += sum(int(m.group(2)) * delta_map[m.group(1)][0] for m in (re.match(r'([de])(\d+)', a) for a in args) if m)
    dy += sum(int(m.group(2)) * delta_map[m.group(1)][1] for m in (re.match(r'([cb])(\d+)', a) for a in args) if m)
    return dx, dy

class CalcCoord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="calc", description="Calcula nova coordenada Wplace com deslocamento.")
    @app_commands.describe(
        input="Coordenadas e deslocamento. Exemplo: (Tl X: 723, Tl Y: 1084, Px X: 539, Px Y: 662) c10 d30"
    )
    async def calc(self, interaction: discord.Interaction, input: str):
        coord_match = re.search(r'\(([^)]+)\)', input)
        if not coord_match:
            await interaction.response.send_message("Formato inválido. Use: (Tl X: 000, Tl Y: 000, Px X: 000, Px Y: 000) c00 d00", ephemeral=True)
            return
        coords = parse_coords(coord_match.group(0))
        if not coords:
            await interaction.response.send_message("Coordenadas inválidas.", ephemeral=True)
            return
        tileX, tileY, pixelX, pixelY = coords
        after = input[coord_match.end():].strip()
        delta_args = after.split()
        direcoes = {
            'c': (':arrow_up:', 'Para cima'),
            'b': (':arrow_down:', 'Para baixo'),
            'e': (':arrow_left:', 'Para esquerda'),
            'd': (':arrow_right:', 'Para direita'),
        }
        deslocamentos_list = []
        for arg in delta_args:
            m = re.match(r'([cbed])(\d+)', arg.lower())
            if m:
                dir_, val = m.group(1), int(m.group(2))
                emoji, texto = direcoes[dir_]
                deslocamentos_list.append(f"{emoji} {texto} {val}")
        deslocamentos = '\n'.join(deslocamentos_list) if deslocamentos_list else 'Nenhum'
        if not (0 <= pixelX < TILE_SIZE and 0 <= pixelY < TILE_SIZE):
            await interaction.response.send_message("Px X e Px Y devem estar entre 0 e 999.", ephemeral=True)
            return
        await interaction.response.defer()
        embed = discord.Embed(title="🧮 Calculadora de Deslocamento Wplace", color=0x2d7ff9)
        embed.add_field(name="📍 Coordenadas iniciais", value=f"Tl X: **{tileX}**, Tl Y: **{tileY}**, Px X: **{pixelX}**, Px Y: **{pixelY}**", inline=False)
        embed.add_field(name="🔀 Deslocamentos", value=deslocamentos, inline=False)
        embed.set_footer(text="O resultado será exibido abaixo.")
        await interaction.edit_original_response(embed=embed)

        globalX, globalY = to_global(tileX, tileY, pixelX, pixelY)
        for arg in delta_args:
            m = re.match(r'([cbed])(\d+)', arg.lower())
            if m:
                dir_, val = m.group(1), int(m.group(2))
                dx, dy = 0, 0
                if dir_ == 'd':
                    dx = val
                elif dir_ == 'e':
                    dx = -val
                elif dir_ == 'b':
                    dy = val
                elif dir_ == 'c':
                    dy = -val
                globalX, globalY = apply_delta(globalX, globalY, dx, dy)
                globalX, globalY, _ = clamp(globalX, globalY)
        newGlobalX, newGlobalY, clamped = clamp(globalX, globalY)
        newTileX, newTileY, newPixelX, newPixelY = to_tile(newGlobalX, newGlobalY)
        resultado = f"📍 Tl X: **{newTileX}**, Tl Y: **{newTileY}**, Px X: **{newPixelX}**, Px Y: **{newPixelY}**"
        if clamped:
            resultado += "\n⚠️ Clamp ativado."
        embed.add_field(name="✅ Resultado", value=resultado, inline=False)
        embed.set_footer(text="Cálculo finalizado.")
        await interaction.edit_original_response(embed=embed)

async def setup(bot):
    await bot.add_cog(CalcCoord(bot))

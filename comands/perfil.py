import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

# ---------------- MODALS -----------------
class SetDescricaoModal(discord.ui.Modal, title="Alterar descrição do perfil"):
    descricao = discord.ui.TextInput(label="Nova descrição", style=discord.TextStyle.paragraph, max_length=200)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect("players.db")
        c = conn.cursor()
        c.execute("UPDATE players SET descricao = ? WHERE discord_id = ?", (str(self.descricao), self.user_id))
        conn.commit()
        conn.close()
        await interaction.response.send_message("✅ Descrição atualizada!", ephemeral=True)

class SetImagemModal(discord.ui.Modal, title="Alterar imagem do perfil"):
    imagem = discord.ui.TextInput(label="URL da imagem", style=discord.TextStyle.short)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect("players.db")
        c = conn.cursor()
        c.execute("UPDATE players SET imagem = ? WHERE discord_id = ?", (str(self.imagem), self.user_id))
        conn.commit()
        conn.close()
        await interaction.response.send_message("✅ Imagem do perfil atualizada!", ephemeral=True)

class SetCorModal(discord.ui.Modal, title="Alterar cor da embed"):
    cor = discord.ui.TextInput(label="Cor em HEX (#ff0000)", style=discord.TextStyle.short, max_length=7)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect("players.db")
        c = conn.cursor()
        c.execute("UPDATE players SET cor = ? WHERE discord_id = ?", (str(self.cor), self.user_id))
        conn.commit()
        conn.close()
        await interaction.response.send_message("✅ Cor atualizada!", ephemeral=True)

# ---------------- BOTÕES -----------------
class PerfilButtons(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Alterar descrição", style=discord.ButtonStyle.primary)
    async def desc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetDescricaoModal(self.user_id))

    @discord.ui.button(label="Alterar imagem", style=discord.ButtonStyle.secondary)
    async def img_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetImagemModal(self.user_id))

    @discord.ui.button(label="Alterar cor", style=discord.ButtonStyle.success)
    async def cor_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetCorModal(self.user_id))

# ---------------- COG -----------------
class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_data(self, user_id):
        conn = sqlite3.connect("players.db")
        c = conn.cursor()
        c.execute(
            "SELECT nick_wplace, brops, descricao, imagem, cor FROM players WHERE discord_id = ?", 
            (str(user_id),)
        )
        resultado = c.fetchone()
        conn.close()
        # Dados padrões caso não exista
        if resultado:
            nick, brops, descricao, imagem, cor = resultado
            if not descricao: descricao = "Sem descrição."
            if not cor: cor = "#00ff00"
            return {"nick": nick, "brops": brops, "descricao": descricao, "imagem": imagem, "cor": cor}
        else:
            return {"nick": "Não vinculado", "brops": 0, "descricao": "Sem descrição.", "imagem": None, "cor": "#00ff00"}

    @app_commands.command(name="perfil", description="Mostra seu perfil estilizado.")
    async def perfil(self, interaction: discord.Interaction):
        user_data = self.get_user_data(interaction.user.id)
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url

        embed = discord.Embed(
            title=f"<:emoji_9:1410103483167674379> Nick WPlace",
            description=f"`{user_data['nick']}`",
            color=discord.Color.from_str(user_data['cor'])
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url="https://cdn.discordapp.com/attachments/1409248231463981159/1416077482305523865/OIP.webp?ex=68c5886d&is=68c436ed&hm=7cb7e72bfddf5773b32894544b65fb1dbdc4226522689e1fcccb34143ccaad25"
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Rank", value="`#1 / 2617 XP\nLVL 16`", inline=False)
        embed.add_field(name="BROPCoins", value=f"`{user_data['brops']}`", inline=False)
        embed.add_field(name="Emblemas", value="Emblemas icons", inline=False)

        if user_data['imagem']:
            embed.set_image(url=user_data['imagem'])

        embed.set_footer(
            text="Feito por ! zenitsu",
            icon_url="https://cdn.discordapp.com/attachments/1409248231463981159/1414731583218520145/5825a5d4609bac3459e976fa6b26a7a3.png?ex=68c54035&is=68c3eeb5&hm=b9203aeba0598c9d283b324926324ec4dc95711d323a6d99bb536f74340ca73d"
        )

        await interaction.response.send_message(embed=embed, view=PerfilButtons(interaction.user.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(Perfil(bot))
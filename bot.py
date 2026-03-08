import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# ─── Config ───────────────────────────────────────────────────────────────────
TOKEN = "MTQ4MDMyODUxNTM0MDczNDcwNw.GYDXIU.Lw-LZwESBAGYxL2MBolooIb2rcd6KpOD_SKXiE"
CURRENCY = "m00d"
COLLECT_AMOUNT = 1000
COLLECT_COOLDOWN = 30 * 60  # 30 minutes in seconds
WORK_MIN = 1000
WORK_MAX = 5000
DATA_FILE = "data.json"
COLOR = 0x00FF00

# ─── Data helpers ─────────────────────────────────────────────────────────────
def load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(data, uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 0, "inventory": [], "last_collect": 0, "last_work": 0}
    return data[uid]

def get_shop(data):
    if "shop" not in data:
        data["shop"] = []
    return data["shop"]

# ─── Bot setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── Sync slash on ready ──────────────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} is online!")

# ══════════════════════════════════════════════════════════════════════════════
#  HELP
# ══════════════════════════════════════════════════════════════════════════════
def help_embed():
    e = discord.Embed(title="📋 قائمة الأوامر", color=COLOR)
    e.add_field(name="💰 الاقتصاد", value=(
        "`balance` — رصيدك\n"
        "`collect` — تجميع 1000 m00d كل 30 دقيقة\n"
        "`work` — اشتغل واكسب بين 1000-5000 m00d\n"
        "`shop` — تصفح المتجر\n"
        "`buy <اسم>` — شراء منتج\n"
        "`inventory` — حقيبتك\n"
        "`leaderboard` — أغنى الأعضاء"
    ), inline=False)
    e.add_field(name="🎮 الألعاب", value=(
        "`game` — قائمة الألعاب\n"
        "`-xo @منافس` — لعبة XO\n"
        "`-flip <heads/tails> <مبلغ>` — رمي العملة\n"
        "`-dice <مبلغ>` — رمي النرد\n"
        "`-slots <مبلغ>` — ماكينة القمار"
    ), inline=False)
    e.add_field(name="🎫 تيكيت", value="`ticket` — فتح تيكيت دعم", inline=False)
    e.add_field(name="👑 أوامر الإدارة", value=(
        "`add item <اسم> <سعر> <وصف>` — إضافة منتج للمتجر\n"
        "`delete item <اسم>` — حذف منتج من المتجر\n"
        "`add money @عضو <مبلغ>` — إضافة رصيد\n"
        "`remove money @عضو <مبلغ>` — خصم رصيد\n"
        "`take item @عضو <اسم>` — أخذ منتج من عضو"
    ), inline=False)
    return e

@bot.command(name="help")
async def help_prefix(ctx):
    await ctx.send(embed=help_embed())

@bot.tree.command(name="help", description="قائمة الأوامر")
async def help_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=help_embed())

# ══════════════════════════════════════════════════════════════════════════════
#  BALANCE
# ══════════════════════════════════════════════════════════════════════════════
def balance_embed(member):
    data = load()
    u = get_user(data, member.id)
    e = discord.Embed(title=f"💰 رصيد {member.display_name}", color=COLOR)
    e.add_field(name="الرصيد", value=f"{u['balance']:,} {CURRENCY}")
    e.set_thumbnail(url=member.display_avatar.url)
    return e

@bot.command(name="balance", aliases=["bal"])
async def balance_prefix(ctx, member: discord.Member = None):
    await ctx.send(embed=balance_embed(member or ctx.author))

@bot.tree.command(name="balance", description="تحقق من رصيدك")
async def balance_slash(interaction: discord.Interaction, member: discord.Member = None):
    await interaction.response.send_message(embed=balance_embed(member or interaction.user))

# ══════════════════════════════════════════════════════════════════════════════
#  COLLECT
# ══════════════════════════════════════════════════════════════════════════════
async def do_collect(uid):
    data = load()
    u = get_user(data, uid)
    now = datetime.now().timestamp()
    diff = now - u["last_collect"]
    if diff < COLLECT_COOLDOWN:
        remaining = int(COLLECT_COOLDOWN - diff)
        m, s = divmod(remaining, 60)
        return False, f"⏳ انتظر **{m}د {s}ث** قبل التجميع مجدداً."
    u["balance"] += COLLECT_AMOUNT
    u["last_collect"] = now
    save(data)
    return True, f"✅ جمعت **{COLLECT_AMOUNT:,} {CURRENCY}**! رصيدك الآن: **{u['balance']:,} {CURRENCY}**"

@bot.command(name="collect")
async def collect_prefix(ctx):
    ok, msg = await do_collect(ctx.author.id)
    await ctx.send(msg)

@bot.tree.command(name="collect", description="اجمع 1000 m00d كل 30 دقيقة")
async def collect_slash(interaction: discord.Interaction):
    ok, msg = await do_collect(interaction.user.id)
    await interaction.response.send_message(msg)

# ══════════════════════════════════════════════════════════════════════════════
#  WORK
# ══════════════════════════════════════════════════════════════════════════════
WORK_MSGS = [
    "عملت مبرمجاً وكسبت", "شغلت سيارة أجرة وكسبت",
    "بعت تمر وكسبت", "صممت موقع وكسبت", "حرست مبنى وكسبت"
]

async def do_work(uid):
    data = load()
    u = get_user(data, uid)
    now = datetime.now().timestamp()
    if now - u["last_work"] < 3600:
        remaining = int(3600 - (now - u["last_work"]))
        m, s = divmod(remaining, 60)
        return f"⏳ انتظر **{m}د {s}ث** قبل العمل مجدداً."
    earned = random.randint(WORK_MIN, WORK_MAX)
    u["balance"] += earned
    u["last_work"] = now
    save(data)
    msg = random.choice(WORK_MSGS)
    return f"💼 {msg} **{earned:,} {CURRENCY}**! رصيدك: **{u['balance']:,} {CURRENCY}**"

@bot.command(name="work")
async def work_prefix(ctx):
    await ctx.send(await do_work(ctx.author.id))

@bot.tree.command(name="work", description="اشتغل واكسب m00d")
async def work_slash(interaction: discord.Interaction):
    await interaction.response.send_message(await do_work(interaction.user.id))

# ══════════════════════════════════════════════════════════════════════════════
#  SHOP
# ══════════════════════════════════════════════════════════════════════════════
def shop_embed(data):
    shop = get_shop(data)
    e = discord.Embed(title="🛒 المتجر", color=COLOR)
    if not shop:
        e.description = "المتجر فارغ حالياً."
    else:
        for item in shop:
            e.add_field(name=f"{item['name']} — {item['price']:,} {CURRENCY}",
                        value=item.get("desc", "لا يوجد وصف"), inline=False)
    return e

@bot.command(name="shop")
async def shop_prefix(ctx):
    data = load()
    await ctx.send(embed=shop_embed(data))

@bot.tree.command(name="shop", description="تصفح المتجر")
async def shop_slash(interaction: discord.Interaction):
    data = load()
    await interaction.response.send_message(embed=shop_embed(data))

# ══════════════════════════════════════════════════════════════════════════════
#  BUY
# ══════════════════════════════════════════════════════════════════════════════
async def do_buy(uid, item_name):
    data = load()
    shop = get_shop(data)
    item = next((i for i in shop if i["name"].lower() == item_name.lower()), None)
    if not item:
        return f"❌ المنتج **{item_name}** غير موجود في المتجر."
    u = get_user(data, uid)
    if u["balance"] < item["price"]:
        return f"❌ رصيدك غير كافٍ. تحتاج **{item['price']:,} {CURRENCY}**."
    u["balance"] -= item["price"]
    u["inventory"].append(item["name"])
    save(data)
    return f"✅ اشتريت **{item['name']}** بـ **{item['price']:,} {CURRENCY}**!"

@bot.command(name="buy")
async def buy_prefix(ctx, *, item_name):
    await ctx.send(await do_buy(ctx.author.id, item_name))

@bot.tree.command(name="buy", description="اشتري منتجاً من المتجر")
@app_commands.describe(item="اسم المنتج")
async def buy_slash(interaction: discord.Interaction, item: str):
    await interaction.response.send_message(await do_buy(interaction.user.id, item))

# ══════════════════════════════════════════════════════════════════════════════
#  INVENTORY
# ══════════════════════════════════════════════════════════════════════════════
def inventory_embed(member, data):
    u = get_user(data, member.id)
    e = discord.Embed(title=f"🎒 حقيبة {member.display_name}", color=COLOR)
    e.description = "\n".join(f"• {i}" for i in u["inventory"]) if u["inventory"] else "الحقيبة فارغة."
    e.set_thumbnail(url=member.display_avatar.url)
    return e

@bot.command(name="inventory", aliases=["inv"])
async def inv_prefix(ctx, member: discord.Member = None):
    data = load()
    await ctx.send(embed=inventory_embed(member or ctx.author, data))

@bot.tree.command(name="inventory", description="شاهد حقيبتك")
async def inv_slash(interaction: discord.Interaction, member: discord.Member = None):
    data = load()
    await interaction.response.send_message(embed=inventory_embed(member or interaction.user, data))

# ══════════════════════════════════════════════════════════════════════════════
#  LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════
async def leaderboard_embed(guild):
    data = load()
    members = {str(m.id): m for m in guild.members}
    scores = []
    for uid, u in data.items():
        if uid in members and isinstance(u, dict) and "balance" in u:
            scores.append((members[uid].display_name, u["balance"]))
    scores.sort(key=lambda x: x[1], reverse=True)
    e = discord.Embed(title="🏆 المتصدرون", color=COLOR)
    medals = ["🥇", "🥈", "🥉"]
    desc = ""
    for i, (name, bal) in enumerate(scores[:10]):
        prefix = medals[i] if i < 3 else f"`{i+1}.`"
        desc += f"{prefix} **{name}** — {bal:,} {CURRENCY}\n"
    e.description = desc or "لا يوجد بيانات."
    return e

@bot.command(name="leaderboard", aliases=["lb", "top"])
async def lb_prefix(ctx):
    await ctx.send(embed=await leaderboard_embed(ctx.guild))

@bot.tree.command(name="leaderboard", description="أغنى الأعضاء")
async def lb_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=await leaderboard_embed(interaction.guild))

# ══════════════════════════════════════════════════════════════════════════════
#  TICKET
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="ticket")
async def ticket_prefix(ctx):
    await create_ticket(ctx.guild, ctx.author, ctx.channel)

@bot.tree.command(name="ticket", description="افتح تيكيت دعم")
async def ticket_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await create_ticket(interaction.guild, interaction.user, None)
    await interaction.followup.send("✅ تم فتح التيكيت!", ephemeral=True)

async def create_ticket(guild, user, reply_channel):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    cat = discord.utils.get(guild.categories, name="Tickets")
    channel = await guild.create_text_channel(
        f"ticket-{user.name}", overwrites=overwrites, category=cat
    )
    e = discord.Embed(title="🎫 تيكيت دعم", description=f"مرحباً {user.mention}!\nاكتب مشكلتك وسيتم مساعدتك.", color=COLOR)

    class CloseButton(discord.ui.View):
        @discord.ui.button(label="إغلاق التيكيت 🔒", style=discord.ButtonStyle.red)
        async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("🔒 سيتم إغلاق التيكيت...")
            await asyncio.sleep(3)
            await channel.delete()

    await channel.send(embed=e, view=CloseButton())
    if reply_channel:
        await reply_channel.send(f"✅ تم فتح تيكيتك في {channel.mention}")

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN: add item / delete item
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="add")
@commands.has_permissions(administrator=True)
async def add_cmd(ctx, category: str, *, rest: str):
    data = load()
    if category.lower() == "item":
        parts = rest.split(" ", 2)
        if len(parts) < 2:
            return await ctx.send("❌ الاستخدام: `!add item <اسم> <سعر> [وصف]`")
        name, price_str = parts[0], parts[1]
        desc = parts[2] if len(parts) > 2 else ""
        try:
            price = int(price_str)
        except:
            return await ctx.send("❌ السعر يجب أن يكون رقماً.")
        shop = get_shop(data)
        shop.append({"name": name, "price": price, "desc": desc})
        save(data)
        await ctx.send(f"✅ تمت إضافة **{name}** للمتجر بسعر **{price:,} {CURRENCY}**.")
    elif category.lower() == "money":
        parts = rest.split()
        if len(parts) < 2 or not ctx.message.mentions:
            return await ctx.send("❌ الاستخدام: `!add money @عضو <مبلغ>`")
        member = ctx.message.mentions[0]
        try:
            amount = int(parts[-1])
        except:
            return await ctx.send("❌ المبلغ يجب أن يكون رقماً.")
        u = get_user(data, member.id)
        u["balance"] += amount
        save(data)
        await ctx.send(f"✅ تمت إضافة **{amount:,} {CURRENCY}** لـ {member.mention}.")

@bot.command(name="delete")
@commands.has_permissions(administrator=True)
async def delete_cmd(ctx, category: str, *, name: str):
    if category.lower() != "item":
        return
    data = load()
    shop = get_shop(data)
    before = len(shop)
    data["shop"] = [i for i in shop if i["name"].lower() != name.lower()]
    save(data)
    if len(data["shop"]) < before:
        await ctx.send(f"✅ تم حذف **{name}** من المتجر.")
    else:
        await ctx.send(f"❌ المنتج **{name}** غير موجود.")

@bot.command(name="remove")
@commands.has_permissions(administrator=True)
async def remove_cmd(ctx, category: str, *, rest: str):
    if category.lower() != "money":
        return
    if not ctx.message.mentions:
        return await ctx.send("❌ الاستخدام: `!remove money @عضو <مبلغ>`")
    data = load()
    member = ctx.message.mentions[0]
    parts = rest.split()
    try:
        amount = int(parts[-1])
    except:
        return await ctx.send("❌ المبلغ يجب أن يكون رقماً.")
    u = get_user(data, member.id)
    u["balance"] = max(0, u["balance"] - amount)
    save(data)
    await ctx.send(f"✅ تم خصم **{amount:,} {CURRENCY}** من {member.mention}.")

@bot.command(name="take")
@commands.has_permissions(administrator=True)
async def take_cmd(ctx, category: str, *, rest: str):
    if category.lower() != "item":
        return
    if not ctx.message.mentions:
        return await ctx.send("❌ الاستخدام: `!take item @عضو <اسم المنتج>`")
    data = load()
    member = ctx.message.mentions[0]
    parts = rest.split(None, 1)
    item_name = parts[1] if len(parts) > 1 else ""
    item_name = item_name.strip()
    u = get_user(data, member.id)
    if item_name in u["inventory"]:
        u["inventory"].remove(item_name)
        save(data)
        await ctx.send(f"✅ تم أخذ **{item_name}** من {member.mention}.")
    else:
        await ctx.send(f"❌ {member.mention} لا يملك **{item_name}**.")

# ══════════════════════════════════════════════════════════════════════════════
#  GAMES LIST
# ══════════════════════════════════════════════════════════════════════════════
def games_embed():
    e = discord.Embed(title="🎮 قائمة الألعاب", color=COLOR)
    e.description = (
        "**-xo @منافس** — لعبة XO ضد لاعب آخر\n"
        "**-flip <heads/tails> <مبلغ>** — رمي العملة للمراهنة\n"
        "**-dice <مبلغ>** — رمي النرد، الأعلى يفوز!\n"
        "**-slots <مبلغ>** — ماكينة القمار 🎰"
    )
    return e

@bot.command(name="game", aliases=["games"])
async def game_prefix(ctx):
    await ctx.send(embed=games_embed())

@bot.tree.command(name="game", description="قائمة الألعاب")
async def game_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=games_embed())

# ══════════════════════════════════════════════════════════════════════════════
#  GAME: COIN FLIP  -flip
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="flip")
async def flip_cmd(ctx, choice: str = None, amount: int = None):
    if not choice or not amount:
        return await ctx.send("❌ الاستخدام: `!-flip <heads/tails> <مبلغ>`")
    if choice.lower() not in ("heads", "tails"):
        return await ctx.send("❌ اختر `heads` أو `tails`.")
    data = load()
    u = get_user(data, ctx.author.id)
    if u["balance"] < amount:
        return await ctx.send("❌ رصيدك غير كافٍ.")
    result = random.choice(["heads", "tails"])
    coin = "👑 Heads" if result == "heads" else "🪙 Tails"
    if choice.lower() == result:
        u["balance"] += amount
        msg = f"✅ {coin} — **ربحت {amount:,} {CURRENCY}!** رصيدك: {u['balance']:,}"
    else:
        u["balance"] -= amount
        msg = f"❌ {coin} — **خسرت {amount:,} {CURRENCY}.** رصيدك: {u['balance']:,}"
    save(data)
    await ctx.send(msg)

# ══════════════════════════════════════════════════════════════════════════════
#  GAME: DICE  -dice
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="dice")
async def dice_cmd(ctx, amount: int = None):
    if not amount:
        return await ctx.send("❌ الاستخدام: `!-dice <مبلغ>`")
    data = load()
    u = get_user(data, ctx.author.id)
    if u["balance"] < amount:
        return await ctx.send("❌ رصيدك غير كافٍ.")
    p = random.randint(1, 6)
    b = random.randint(1, 6)
    e = discord.Embed(title="🎲 لعبة النرد", color=COLOR)
    e.add_field(name="أنت", value=f"🎲 {p}")
    e.add_field(name="البوت", value=f"🎲 {b}")
    if p > b:
        u["balance"] += amount
        e.description = f"✅ **فزت بـ {amount:,} {CURRENCY}!**"
    elif p < b:
        u["balance"] -= amount
        e.description = f"❌ **خسرت {amount:,} {CURRENCY}.**"
    else:
        e.description = "🤝 **تعادل! لا خسارة ولا ربح.**"
    save(data)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════════════════════════════
#  GAME: SLOTS  -slots
# ══════════════════════════════════════════════════════════════════════════════
SLOT_ITEMS = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]

@bot.command(name="slots")
async def slots_cmd(ctx, amount: int = None):
    if not amount:
        return await ctx.send("❌ الاستخدام: `!-slots <مبلغ>`")
    data = load()
    u = get_user(data, ctx.author.id)
    if u["balance"] < amount:
        return await ctx.send("❌ رصيدك غير كافٍ.")
    s = [random.choice(SLOT_ITEMS) for _ in range(3)]
    e = discord.Embed(title="🎰 ماكينة القمار", color=COLOR)
    e.description = f"[ {s[0]} | {s[1]} | {s[2]} ]"
    if s[0] == s[1] == s[2]:
        win = amount * 3
        u["balance"] += win
        e.add_field(name="النتيجة", value=f"🎉 **JACKPOT! ربحت {win:,} {CURRENCY}!**")
    elif s[0] == s[1] or s[1] == s[2] or s[0] == s[2]:
        win = amount
        u["balance"] += win
        e.add_field(name="النتيجة", value=f"✅ **زوج! ربحت {win:,} {CURRENCY}!**")
    else:
        u["balance"] -= amount
        e.add_field(name="النتيجة", value=f"❌ **خسرت {amount:,} {CURRENCY}.**")
    save(data)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════════════════════════════
#  GAME: XO  -xo
# ══════════════════════════════════════════════════════════════════════════════
xo_games = {}

def render_board(board):
    symbols = {0: "⬜", 1: "❌", 2: "⭕"}
    rows = []
    for i in range(0, 9, 3):
        rows.append(" ".join(symbols[board[i+j]] for j in range(3)))
    return "\n".join(rows)

def check_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] != 0:
            return board[a]
    if 0 not in board:
        return -1
    return 0

class XOView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__(timeout=60)
        self.game_id = game_id
        for i in range(9):
            btn = discord.ui.Button(label="​", row=i//3, custom_id=str(i))
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, idx):
        async def callback(interaction: discord.Interaction):
            game = xo_games.get(self.game_id)
            if not game:
                return await interaction.response.send_message("❌ اللعبة انتهت.", ephemeral=True)
            current = game["players"][game["turn"]-1]
            if interaction.user.id != current:
                return await interaction.response.send_message("❌ ليس دورك!", ephemeral=True)
            if game["board"][idx] != 0:
                return await interaction.response.send_message("❌ هذه الخانة مشغولة.", ephemeral=True)
            game["board"][idx] = game["turn"]
            winner = check_winner(game["board"])
            symbols = {0: "⬜", 1: "❌", 2: "⭕"}
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.custom_id == str(idx):
                    item.label = symbols[game["turn"]]
                    item.disabled = True
            if winner != 0:
                for item in self.children:
                    item.disabled = True
                if winner == -1:
                    msg = "🤝 **تعادل!**"
                else:
                    name = interaction.guild.get_member(game["players"][winner-1]).display_name
                    msg = f"🏆 **{name} فاز!**"
                del xo_games[self.game_id]
                await interaction.response.edit_message(content=f"{render_board(game['board'])}\n\n{msg}", view=self)
            else:
                game["turn"] = 2 if game["turn"] == 1 else 1
                next_p = interaction.guild.get_member(game["players"][game["turn"]-1])
                await interaction.response.edit_message(
                    content=f"{render_board(game['board'])}\n\n🎮 دور {next_p.mention} ({'❌' if game['turn']==1 else '⭕'})",
                    view=self
                )
        return callback

@bot.command(name="xo")
async def xo_cmd(ctx, opponent: discord.Member = None):
    if not opponent or opponent.bot or opponent == ctx.author:
        return await ctx.send("❌ اذكر منافساً صحيحاً.")
    game_id = f"{ctx.author.id}-{opponent.id}"
    xo_games[game_id] = {
        "players": [ctx.author.id, opponent.id],
        "board": [0]*9,
        "turn": 1
    }
    view = XOView(game_id)
    await ctx.send(
        content=f"⬜⬜⬜\n⬜⬜⬜\n⬜⬜⬜\n\n🎮 دور {ctx.author.mention} (❌)",
        view=view
    )

# ══════════════════════════════════════════════════════════════════════════════
#  Handle - prefix for games (e.g. !-xo, !-flip, !-dice, !-slots)
# ══════════════════════════════════════════════════════════════════════════════
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.strip()
    # Handle -xo, -flip, -dice, -slots as !-xo etc.
    if content.startswith("-"):
        message.content = "!" + content
    await bot.process_commands(message)

bot.run(TOKEN)

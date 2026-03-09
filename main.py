import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import json
import os
import random
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# ═══════════════════════════════════════════════════════════
#  إعدادات البوت
# ═══════════════════════════════════════════════════════════
PREFIX = "!"
TOKEN = os.environ.get("TOKEN") or os.environ.get("DISCORD_TOKEN") or "YOUR_TOKEN_HERE"
LIME_COLOR = 0x00FF00

# IDs
WELCOME_CHANNEL_ID = 1470539807074549850
GOODBYE_CHANNEL_ID = 1470539840314671134
YOUTUBE_CHANNEL_ID = 1470540807663517838
AUTO_ROLE_ID = 1471338474652045403

# YouTube Channel
YOUTUBE_CHANNEL_NAME = "Fttz_edit"
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")  # اختياري

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ═══════════════════════════════════════════════════════════
#  حفظ البيانات
# ═══════════════════════════════════════════════════════════
def load_data():
    if not os.path.exists("data.json"):
        return {}
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "mood": 0,
            "xp": 0,
            "level": 1,
            "last_collect": 0,
            "last_work": 0,
            "chat_messages": 0,
            "voice_minutes": 0,
            "inventory": [],
            "warnings": []
        }
    return data[uid]

# ═══════════════════════════════════════════════════════════
#  الشوب الكامل
# ═══════════════════════════════════════════════════════════
SHOP_ITEMS = [
    # 🍽️ أكلات
    {"id": "burger", "name": "🍔 برجر", "price": 150, "category": "أكل"},
    {"id": "pizza", "name": "🍕 بيتزا", "price": 300, "category": "أكل"},
    {"id": "shawarma", "name": "🌯 شاورما", "price": 200, "category": "أكل"},
    {"id": "couscous", "name": "🍲 كسكسي", "price": 500, "category": "أكل"},
    {"id": "sushi", "name": "🍣 سوشي", "price": 800, "category": "أكل"},
    {"id": "kebab", "name": "🍢 كباب", "price": 400, "category": "أكل"},
    {"id": "biryani", "name": "🍛 برياني", "price": 600, "category": "أكل"},
    {"id": "steak", "name": "🥩 ستيك", "price": 900, "category": "أكل"},
    {"id": "ramen", "name": "🍜 رامن", "price": 700, "category": "أكل"},
    {"id": "tacos", "name": "🌮 تاكو", "price": 250, "category": "أكل"},
    
    # 🔫 أسلحة وحربي (كثير!)
    {"id": "knife", "name": "🔪 سكين", "price": 1000, "category": "حربي"},
    {"id": "machete", "name": "🗡️ ساطور", "price": 2500, "category": "حربي"},
    {"id": "pistol", "name": "🔫 مسدس", "price": 5000, "category": "حربي"},
    {"id": "revolver", "name": "🔫 ريفولفر", "price": 7500, "category": "حربي"},
    {"id": "smg", "name": "💥 رشاش خفيف", "price": 12000, "category": "حربي"},
    {"id": "rifle", "name": "🎯 بندقية", "price": 15000, "category": "حربي"},
    {"id": "sniper", "name": "🎯 سنايبر", "price": 25000, "category": "حربي"},
    {"id": "shotgun", "name": "💥 شوتجن", "price": 18000, "category": "حربي"},
    {"id": "ak47", "name": "🔫 AK-47", "price": 30000, "category": "حربي"},
    {"id": "m4a1", "name": "🔫 M4A1", "price": 35000, "category": "حربي"},
    {"id": "rpg", "name": "🚀 آر بي جي", "price": 75000, "category": "حربي"},
    {"id": "grenade", "name": "💣 قنبلة", "price": 5000, "category": "حربي"},
    {"id": "c4", "name": "💣 C4", "price": 15000, "category": "حربي"},
    {"id": "mine", "name": "💥 لغم", "price": 8000, "category": "حربي"},
    {"id": "armor", "name": "🛡️ درع واقي", "price": 20000, "category": "حربي"},
    {"id": "helmet", "name": "⛑️ خوذة", "price": 10000, "category": "حربي"},
    {"id": "tank", "name": "🚛 دبابة", "price": 500000, "category": "حربي"},
    {"id": "helicopter", "name": "🚁 هليكوبتر حربية", "price": 1000000, "category": "حربي"},
    {"id": "fighter_jet", "name": "✈️ طائرة حربية", "price": 2000000, "category": "حربي"},
    {"id": "battleship", "name": "🚢 سفينة حربية", "price": 5000000, "category": "حربي"},
    {"id": "submarine", "name": "⚓ غواصة", "price": 3000000, "category": "حربي"},
    {"id": "drone", "name": "🛸 درون قتالي", "price": 250000, "category": "حربي"},
    {"id": "nuke", "name": "☢️ صاروخ نووي", "price": 100000000, "category": "حربي"},
    
    # 📱 إلكترونيات
    {"id": "phone", "name": "📱 هاتف", "price": 15000, "category": "إلكترونيات"},
    {"id": "iphone", "name": "📱 آيفون", "price": 35000, "category": "إلكترونيات"},
    {"id": "laptop", "name": "💻 لابتوب", "price": 50000, "category": "إلكترونيات"},
    {"id": "macbook", "name": "💻 ماك بوك", "price": 80000, "category": "إلكترونيات"},
    {"id": "tv", "name": "📺 تلفزيون", "price": 20000, "category": "إلكترونيات"},
    {"id": "ps5", "name": "🎮 PS5", "price": 25000, "category": "إلكترونيات"},
    {"id": "xbox", "name": "🎮 Xbox", "price": 25000, "category": "إلكترونيات"},
    {"id": "camera", "name": "📷 كاميرا", "price": 40000, "category": "إلكترونيات"},
    {"id": "drone_cam", "name": "🛸 درون تصوير", "price": 60000, "category": "إلكترونيات"},
    {"id": "vr", "name": "🥽 نظارة VR", "price": 30000, "category": "إلكترونيات"},
    
    # 🚗 سيارات
    {"id": "bike", "name": "🏍️ دراجة نارية", "price": 80000, "category": "سيارات"},
    {"id": "scooter", "name": "🛴 سكوتر", "price": 15000, "category": "سيارات"},
    {"id": "car", "name": "🚗 سيارة عادية", "price": 300000, "category": "سيارات"},
    {"id": "suv", "name": "🚙 SUV", "price": 500000, "category": "سيارات"},
    {"id": "sports_car", "name": "🏎️ سيارة رياضية", "price": 900000, "category": "سيارات"},
    {"id": "ferrari", "name": "🏎️ فيراري", "price": 2000000, "category": "سيارات"},
    {"id": "lamborghini", "name": "🏎️ لامبورغيني", "price": 2500000, "category": "سيارات"},
    {"id": "bugatti", "name": "🏎️ بوغاتي", "price": 5000000, "category": "سيارات"},
    {"id": "limo", "name": "🚙 ليموزين", "price": 1500000, "category": "سيارات"},
    {"id": "truck", "name": "🚚 شاحنة", "price": 600000, "category": "سيارات"},
    
    # 🏠 عقارات
    {"id": "apartment", "name": "🏠 شقة", "price": 1000000, "category": "عقارات"},
    {"id": "villa", "name": "🏰 فيلا", "price": 5000000, "category": "عقارات"},
    {"id": "island", "name": "🏝️ جزيرة خاصة", "price": 50000000, "category": "عقارات"},
    
    # 💍 كماليات
    {"id": "watch", "name": "⌚ ساعة فاخرة", "price": 100000, "category": "كماليات"},
    {"id": "ring", "name": "💍 خاتم ألماس", "price": 500000, "category": "كماليات"},
    {"id": "yacht", "name": "🛥️ يخت", "price": 10000000, "category": "كماليات"},
]

# ═══════════════════════════════════════════════════════════
#  نظام التيكتات
# ═══════════════════════════════════════════════════════════
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="دعم فني | Support", emoji="🛠️", value="support"),
            discord.SelectOption(label="تقديم طلب | Application", emoji="📝", value="application"),
            discord.SelectOption(label="بلاغات | Reports", emoji="⚠️", value="report"),
            discord.SelectOption(label="شكوى | Complaint", emoji="📢", value="complaint"),
        ]
        super().__init__(placeholder="اختر نوع التيكت | Select type", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        category = discord.utils.get(interaction.guild.categories, name="📩 Tickets")
        if not category:
            category = await interaction.guild.create_category("📩 Tickets")
        
        for ch in category.text_channels:
            if ch.topic and str(interaction.user.id) in ch.topic:
                await interaction.followup.send(f"❌ عندك تيكت مفتوح!\n{ch.mention}", ephemeral=True)
                return
        
        ticket_num = len(category.text_channels) + 1
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await category.create_text_channel(
            name=f"ticket-{ticket_num}",
            overwrites=overwrites,
            topic=f"{interaction.user.id}|{self.values[0]}"
        )
        
        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_num}",
            description=f"مرحباً {interaction.user.mention}!\nاشرح مشكلتك هنا ✨",
            color=LIME_COLOR
        )
        
        close_btn = Button(label="🔒 إغلاق", style=discord.ButtonStyle.danger)
        async def close_cb(i):
            if i.user.id != interaction.user.id and not i.user.guild_permissions.manage_channels:
                return await i.response.send_message("❌ ما عندك صلاحية!", ephemeral=True)
            
            del_btn = Button(label="🗑️ حذف", style=discord.ButtonStyle.danger)
            cancel_btn = Button(label="❌ إلغاء", style=discord.ButtonStyle.secondary)
            
            async def del_cb(ii):
                await ii.response.send_message("🗑️ جاري الحذف...", ephemeral=True)
                await asyncio.sleep(2)
                await channel.delete()
            
            async def cancel_cb(ii):
                await ii.response.send_message("❌ تم الإلغاء", ephemeral=True)
            
            del_btn.callback = del_cb
            cancel_btn.callback = cancel_cb
            v = View()
            v.add_item(del_btn)
            v.add_item(cancel_btn)
            await i.response.send_message("⚠️ تأكيد الحذف؟", view=v, ephemeral=True)
        
        close_btn.callback = close_cb
        v = View(timeout=None)
        v.add_item(close_btn)
        
        await channel.send(embed=embed, view=v)
        await interaction.followup.send(f"✅ تم! {channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ═══════════════════════════════════════════════════════════
#  ألعاب
# ═══════════════════════════════════════════════════════════
# XO Game
class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
    
    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user != view.current_player:
            return await interaction.response.send_message("❌ مو دورك!", ephemeral=True)
        
        if self.label != "\u200b":
            return await interaction.response.send_message("❌ مكان محجوز!", ephemeral=True)
        
        self.label = view.current_mark
        self.style = discord.ButtonStyle.primary if view.current_mark == "X" else discord.ButtonStyle.danger
        
        view.board[self.y][self.x] = view.current_mark
        
        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"🎉 {view.current_player.mention} فاز!", view=view)
        elif all(all(cell != " " for cell in row) for row in view.board):
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content="🤝 تعادل!", view=view)
        else:
            view.current_player = view.player2 if view.current_player == view.player1 else view.player1
            view.current_mark = "O" if view.current_mark == "X" else "X"
            await interaction.response.edit_message(content=f"دور {view.current_player.mention} ({view.current_mark})", view=view)

class TicTacToeView(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=300)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_mark = "X"
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))
    
    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != " ":
                return True
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != " ":
                return True
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            return True
        return False

# ═══════════════════════════════════════════════════════════
#  Bot Events
# ═══════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    
    bot.add_view(TicketView())

@bot.event
async def on_member_join(member):
    # Auto role
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass
    
    # Welcome
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title="🎉 أهلاً وسهلاً!",
            description=f"مرحباً {member.mention} في السيرفر! 🌟",
            color=LIME_COLOR
        )
        await ch.send(embed=embed)

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(GOODBYE_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="👋 وداعاً!", description=f"غادر {member.name}", color=0xFF5555)
        await ch.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content = message.content.strip().lower()
    
    # Greetings
    if content in ["هلا", "اهلا", "أهلا", "هلا اهلا"]:
        await message.channel.send(f"هلا كيفك {message.author.mention} 👋😊")
    elif content in ["سلام عليكم", "السلام عليكم", "سلام عليكم ورحمة الله وبركاته", "السلام عليكم ورحمة الله وبركاته"]:
        await message.channel.send(f"وعليكم السلام ورحمة الله وبركاته {message.author.mention}")
    elif content in ["hi", "hello"]:
        await message.channel.send(f"hi, what's up {message.author.mention}")
    
    # XP
    data = load_data()
    user = get_user(data, message.author.id)
    user["chat_messages"] = user.get("chat_messages", 0) + 1
    
    xp = random.randint(5, 15)
    user["xp"] += xp
    level = user["level"]
    needed = level * 100
    
    if user["xp"] >= needed:
        user["xp"] -= needed
        user["level"] += 1
        await message.channel.send(f"🎉 {message.author.mention} وصل لفل **{user['level']}**!")
    
    save_data(data)
    await bot.process_commands(message)

# ═══════════════════════════════════════════════════════════
#  SLASH COMMANDS - Economy
# ═══════════════════════════════════════════════════════════
@bot.tree.command(name="collect")
async def collect(interaction: discord.Interaction):
    """اجمع m00d كل 30 دقيقة"""
    data = load_data()
    user = get_user(data, interaction.user.id)
    now = time.time()
    cd = 30 * 60
    
    if now - user["last_collect"] < cd:
        remaining = cd - (now - user["last_collect"])
        m = int(remaining // 60)
        s = int(remaining % 60)
        return await interaction.response.send_message(f"⏳ انتظر {m}:{s:02d}", ephemeral=True)
    
    earned = random.randint(100, 1000)
    user["mood"] += earned
    user["last_collect"] = now
    save_data(data)
    
    embed = discord.Embed(title="💰 Collected!", description=f"+**{earned:,} m00d**\n💵 {user['mood']:,} m00d", color=LIME_COLOR)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="work")
async def work(interaction: discord.Interaction):
    """اشتغل واكسب 10K-100K"""
    data = load_data()
    user = get_user(data, interaction.user.id)
    now = time.time()
    cd = 60 * 60
    
    if now - user.get("last_work", 0) < cd:
        m = int((cd - (now - user["last_work"])) // 60)
        return await interaction.response.send_message(f"⏳ ارتح {m} دقيقة", ephemeral=True)
    
    jobs = [("👨‍🍳 طباخ", "طبخت"), ("🚗 سائق", "وصلت زبائن"), ("💻 مبرمج", "كتبت كود")]
    job, desc = random.choice(jobs)
    earned = random.randint(10000, 100000)
    user["mood"] += earned
    user["last_work"] = now
    save_data(data)
    
    embed = discord.Embed(title=f"💼 {job}", description=f"{desc}\n+**{earned:,} m00d**\n💵 {user['mood']:,} m00d", color=LIME_COLOR)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="balance")
async def balance(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """شوف رصيدك"""
    member = member or interaction.user
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(title=f"💳 {member.display_name}", description=f"**{user['mood']:,} m00d**", color=LIME_COLOR)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    """أغنى الأعضاء"""
    data = load_data()
    members = {str(m.id): m for m in interaction.guild.members}
    top = sorted([(uid, d) for uid, d in data.items() if uid in members], key=lambda x: x[1].get("mood", 0), reverse=True)[:10]
    
    embed = discord.Embed(title="🏆 Richest Members", color=LIME_COLOR)
    medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(top):
        m = members.get(uid)
        name = m.display_name if m else f"User#{uid}"
        desc += f"{medals[i]} **{name}** — {d.get('mood',0):,} m00d\n"
    embed.description = desc or "No data"
    await interaction.response.send_message(embed=embed)

# ═══════════════════════════════════════════════════════════
#  SLASH COMMANDS - Shop
# ═══════════════════════════════════════════════════════════
@bot.tree.command(name="shop")
async def shop_cmd(interaction: discord.Interaction, category: Optional[str] = None):
    """الشوب الكامل"""
    categories = {}
    for item in SHOP_ITEMS:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    if not category:
        embed = discord.Embed(title="🏪 الشوب", color=LIME_COLOR)
        for cat in categories:
            embed.add_field(name=f"📂 {cat}", value=f"`/shop category:{cat}`", inline=True)
        return await interaction.response.send_message(embed=embed)
    
    items = categories.get(category, [])
    if not items:
        return await interaction.response.send_message("❌ فئة غير موجودة!", ephemeral=True)
    
    embed = discord.Embed(title=f"🏪 {category}", color=LIME_COLOR)
    for item in items:
        embed.add_field(name=item["name"], value=f"💰 {item['price']:,} m00d\n`/buy item:{item['id']}`", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="buy")
async def buy_cmd(interaction: discord.Interaction, item: str):
    """اشتري من الشوب"""
    item_obj = next((i for i in SHOP_ITEMS if i["id"] == item), None)
    if not item_obj:
        return await interaction.response.send_message("❌ العنصر غير موجود!", ephemeral=True)
    
    data = load_data()
    user = get_user(data, interaction.user.id)
    
    if user["mood"] < item_obj["price"]:
        needed = item_obj["price"] - user["mood"]
        return await interaction.response.send_message(f"❌ تحتاج {needed:,} m00d أكثر!", ephemeral=True)
    
    user["mood"] -= item_obj["price"]
    user["inventory"].append(item)
    save_data(data)
    
    embed = discord.Embed(title="✅ تم الشراء!", description=f"{item_obj['name']}\n💵 {user['mood']:,} m00d", color=LIME_COLOR)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventory")
async def inventory_cmd(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """شوف المخزن"""
    member = member or interaction.user
    data = load_data()
    user = get_user(data, member.id)
    inv = user.get("inventory", [])
    
    if not inv:
        return await interaction.response.send_message(f"🎒 {member.display_name} مخزنه فاضي!")
    
    counts = {}
    for iid in inv:
        counts[iid] = counts.get(iid, 0) + 1
    
    desc = ""
    for iid, count in counts.items():
        item = next((i for i in SHOP_ITEMS if i["id"] == iid), None)
        if item:
            desc += f"{item['name']} x{count}\n"
    
    embed = discord.Embed(title=f"🎒 {member.display_name}", description=desc, color=LIME_COLOR)
    await interaction.response.send_message(embed=embed)

# ═══════════════════════════════════════════════════════════
#  SLASH COMMANDS - Moderation
# ═══════════════════════════════════════════════════════════
@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_cmd(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason"):
    """طرد عضو"""
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم طرد {member.mention}\nالسبب: {reason}")

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_cmd(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason"):
    """إخراج عضو"""
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 تم إخراج {member.mention}\nالسبب: {reason}")

@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_cmd(interaction: discord.Interaction, amount: int):
    """مسح رسائل"""
    if amount < 1 or amount > 100:
        return await interaction.response.send_message("❌ 1-100 فقط!", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ تم مسح {len(deleted)} رسالة", ephemeral=True)

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn_cmd(interaction: discord.Interaction, member: discord.Member, reason: str):
    """إنذار عضو"""
    data = load_data()
    user = get_user(data, member.id)
    user["warnings"].append({"reason": reason, "by": interaction.user.id, "time": time.time()})
    save_data(data)
    
    count = len(user["warnings"])
    await interaction.response.send_message(f"⚠️ {member.mention} تم إنذاره!\nالسبب: {reason}\nالإنذارات: {count}")

# ═══════════════════════════════════════════════════════════
#  SLASH COMMANDS - Games
# ═══════════════════════════════════════════════════════════
@bot.tree.command(name="xo")
async def xo_cmd(interaction: discord.Interaction, opponent: discord.Member):
    """XO لعبة"""
    if opponent.bot:
        return await interaction.response.send_message("❌ ما تقدر تلعب مع بوت!", ephemeral=True)
    if opponent == interaction.user:
        return await interaction.response.send_message("❌ ما تقدر تلعب مع نفسك!", ephemeral=True)
    
    view = TicTacToeView(interaction.user, opponent)
    await interaction.response.send_message(f"🎮 XO Game!\n{interaction.user.mention} (X) vs {opponent.mention} (O)\nدور {interaction.user.mention}", view=view)

@bot.tree.command(name="guess")
async def guess_cmd(interaction: discord.Interaction):
    """لعبة تخمين الرقم"""
    number = random.randint(1, 100)
    await interaction.response.send_message("🎲 خمّن رقم من 1-100!\nعندك 6 محاولات")
    
    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()
    
    attempts = 0
    while attempts < 6:
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            guess = int(msg.content)
            attempts += 1
            
            if guess == number:
                data = load_data()
                user = get_user(data, interaction.user.id)
                prize = 5000
                user["mood"] += prize
                save_data(data)
                return await interaction.channel.send(f"🎉 صحيح! الرقم {number}\n+{prize:,} m00d")
            elif guess < number:
                await interaction.channel.send(f"📈 أعلى! ({6-attempts} محاولات متبقية)")
            else:
                await interaction.channel.send(f"📉 أقل! ({6-attempts} محاولات متبقية)")
        except asyncio.TimeoutError:
            return await interaction.channel.send(f"⏰ انتهى الوقت! الرقم كان {number}")
    
    await interaction.channel.send(f"❌ خسرت! الرقم كان {number}")

# ═══════════════════════════════════════════════════════════
#  SLASH COMMANDS - Tickets & Admin
# ═══════════════════════════════════════════════════════════
@bot.tree.command(name="setup")
@app_commands.checks.has_permissions(administrator=True)
async def setup_cmd(interaction: discord.Interaction, channel: discord.TextChannel):
    """إعداد التيكتات"""
    embed = discord.Embed(
        title="🎫 نظام التيكتات",
        description="اختر نوع التيكت من القائمة",
        color=LIME_COLOR
    )
    view = TicketView()
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ تم! {channel.mention}", ephemeral=True)

@bot.tree.command(name="add")
@app_commands.checks.has_permissions(administrator=True)
async def add_cmd(interaction: discord.Interaction, member: discord.Member, amount: int):
    """أضف m00d"""
    data = load_data()
    user = get_user(data, member.id)
    user["mood"] += amount
    save_data(data)
    await interaction.response.send_message(f"✅ +{amount:,} m00d → {member.mention}\n💵 {user['mood']:,} m00d")

@bot.tree.command(name="remove")
@app_commands.checks.has_permissions(administrator=True)
async def remove_cmd(interaction: discord.Interaction, member: discord.Member, amount: int):
    """اسحب m00d"""
    data = load_data()
    user = get_user(data, member.id)
    user["mood"] = max(0, user["mood"] - amount)
    save_data(data)
    await interaction.response.send_message(f"✅ -{amount:,} m00d → {member.mention}\n💵 {user['mood']:,} m00d")

@bot.tree.command(name="help")
async def help_cmd(interaction: discord.Interaction):
    """أوامر البوت"""
    embed = discord.Embed(title="📖 Commands", color=LIME_COLOR)
    embed.add_field(name="💰 Economy", value="`/collect` `/work` `/balance` `/shop` `/buy` `/inventory`", inline=False)
    embed.add_field(name="🎮 Games", value="`/xo @user` `/guess`", inline=False)
    embed.add_field(name="🛡️ Moderation", value="`/ban` `/kick` `/clear` `/warn`", inline=False)
    embed.add_field(name="👑 Admin", value="`/setup` `/add` `/remove`", inline=False)
    await interaction.response.send_message(embed=embed)

# ═══════════════════════════════════════════════════════════
#  PREFIX COMMANDS (! support)
# ═══════════════════════════════════════════════════════════
@bot.command()
async def collect(ctx):
    await ctx.invoke(bot.get_command("collect"))

@bot.command()
async def work(ctx):
    await ctx.invoke(bot.get_command("work"))

@bot.command()
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(title=f"💳 {member.display_name}", description=f"**{user['mood']:,} m00d**", color=LIME_COLOR)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📖 Commands", color=LIME_COLOR)
    embed.add_field(name="💰 Economy", value="`!collect` `!work` `!balance`\n(استخدم `/` للمزيد)", inline=False)
    embed.add_field(name="✨ Tip", value="جرّب `/help` لكل الأوامر!", inline=False)
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════════
#  RUN BOT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)

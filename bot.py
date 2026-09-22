import os
import json
import time
import random
import requests
import html as _html
from datetime import datetime
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "8764499213"))
ADMIN_IDS = [OWNER_ID]
PORT = int(os.environ.get("PORT", 10000))

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not set!")
    exit(1)

print("✅ Bot token loaded!")
print(f"👑 Owner ID: {OWNER_ID}")

bot = TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# ============================================================
# FILES & DATA
# ============================================================
USERS_FILE = "users.json"
PENDING_FILE = "pending.json"
SETTINGS_FILE = "settings.json"
BALANCE_FILE = "balance.json"

# ============================================================
# EMOJI MAPPING
# ============================================================
EMOJI_MAPPING = {
    "✅": ["6246537187614005254", "6246782404476803545"],
    "⭐": ["6244496562752331516", "5904618938578243567"],
    "💎": ["6086778246882399112", "5791697221799907788"],
    "💰": ["6089104607328342288", "6086730718774300509"],
    "👑": ["5794422335599546668", "6089003761496232797"],
    "🔥": ["4956222745814762495", "4956606007221421405"],
    "⚡": ["5791970059597386804", "6087079590377820415"],
    "❤️": ["5783157259152397008", "5801084710343938087"],
    "🎯": ["6244496562752331516"],
    "💳": ["6089140105233044310"],
    "🔔": ["6035070298087231243"],
    "✅": ["6246537187614005254"],
}

FLAG_MAPPING = {
    "🇮🇳": "5433601609076586221",
    "🇺🇸": "5433865586356531140",
}

# ============================================================
# HELPERS
# ============================================================
def stylish_text(text: str) -> str:
    stylish_chars = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }
    result = ""
    for char in text:
        result += stylish_chars.get(char, char)
    return result

def _utf16_len(ch: str) -> int:
    return len(ch.encode("utf-16-le")) // 2

def _utf16_len_str(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2

def _build_pe_entities(text: str):
    entities = []
    utf16_offset = 0
    total_utf16 = _utf16_len_str(text)
    
    if total_utf16 > 0:
        entities.append(MessageEntity(type="bold", offset=0, length=total_utf16))
    
    i = 0
    while i < len(text):
        ch = text[i]
        ch_len = _utf16_len(ch)
        
        if ch in EMOJI_MAPPING:
            eid = int(random.choice(EMOJI_MAPPING[ch]))
            entities.append(MessageEntity(
                type="custom_emoji",
                offset=utf16_offset,
                length=ch_len,
                custom_emoji_id=eid
            ))
        elif ch in FLAG_MAPPING:
            eid = int(FLAG_MAPPING[ch])
            entities.append(MessageEntity(
                type="custom_emoji",
                offset=utf16_offset,
                length=ch_len,
                custom_emoji_id=eid
            ))
        utf16_offset += ch_len
        i += 1
    
    return entities

def _send_pe(chat_id, text: str, reply_markup=None):
    try:
        entities = _build_pe_entities(text)
        return bot.send_message(chat_id, text, entities=entities, reply_markup=reply_markup, parse_mode=None)
    except:
        return bot.send_message(chat_id, text, reply_markup=reply_markup)

# ============================================================
# DATA FUNCTIONS
# ============================================================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_balance():
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_balance(balance):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balance, f, indent=2)

def load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_pending(pending):
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2)

def load_settings():
    default = {
        "upi": "vanshx111@naviaxis",
        "developer": "@iflexzyann",
        "support": "@iflexzyann",
        "welcome_image": "https://iili.io/C8DNTyQ.jpg",
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for key, val in default.items():
                    if key not in data:
                        data[key] = val
                return data
        except:
            pass
    save_settings(default)
    return default

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# ============================================================
# HELPERS
# ============================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id))

def get_balance(user_id):
    balance = load_balance()
    return balance.get(str(user_id), 0)

def set_balance(user_id, amount):
    balance = load_balance()
    balance[str(user_id)] = amount
    save_balance(balance)

def add_balance(user_id, amount):
    balance = load_balance()
    current = balance.get(str(user_id), 0)
    balance[str(user_id)] = current + amount
    save_balance(balance)
    return balance[str(user_id)]

def register_user(user_id, username=None, first_name=None):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "id": user_id,
            "username": username,
            "name": first_name or "Unknown",
            "phone": None,
            "verified": False,
            "banned": False,
            "joined": datetime.now().isoformat()
        }
        save_users(users)
        return users[str(user_id)]
    return users[str(user_id)]

def update_user(user_id, key, value):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)][key] = value
        save_users(users)

def notify_owner(msg):
    try:
        bot.send_message(OWNER_ID, msg)
    except:
        pass

def notify_admins(msg):
    for admin in ADMIN_IDS:
        try:
            bot.send_message(admin, msg)
        except:
            pass

# ============================================================
# BUTTONS
# ============================================================
def make_green_button(text: str, callback: str = None, url: str = None):
    final_text = stylish_text(text)
    try:
        if callback:
            return InlineKeyboardButton(text=final_text, style="success", callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final_text, style="success", url=url)
        else:
            return InlineKeyboardButton(text=final_text, style="success")
    except:
        if callback:
            return InlineKeyboardButton(text=final_text, callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final_text, url=url)
        else:
            return InlineKeyboardButton(text=final_text)

def make_red_button(text: str, callback: str = None, url: str = None):
    final_text = stylish_text(text)
    try:
        if callback:
            return InlineKeyboardButton(text=final_text, style="danger", callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final_text, style="danger", url=url)
        else:
            return InlineKeyboardButton(text=final_text, style="danger")
    except:
        if callback:
            return InlineKeyboardButton(text=final_text, callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final_text, url=url)
        else:
            return InlineKeyboardButton(text=final_text)

# ============================================================
# USER MENU
# ============================================================
def get_user_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton(stylish_text("💰 ADD BALANCE")))
    markup.row(KeyboardButton(stylish_text("💳 CHECK BALANCE")), KeyboardButton(stylish_text("💸 TRANSFER BALANCE")))
    markup.row(KeyboardButton(stylish_text("🆘 SUPPORT")), KeyboardButton(stylish_text("ℹ️ HELP")))
    return markup

# ============================================================
# ADMIN MENU
# ============================================================
def get_admin_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton(stylish_text("👥 ALL USERS")), KeyboardButton(stylish_text("📊 STATS")))
    markup.row(KeyboardButton(stylish_text("💸 SEND BALANCE")), KeyboardButton(stylish_text("🚫 BAN USER")))
    markup.row(KeyboardButton(stylish_text("✅ UNBAN USER")), KeyboardButton(stylish_text("⚙️ SET UPI")))
    markup.row(KeyboardButton(stylish_text("📢 BROADCAST")), KeyboardButton(stylish_text("ℹ️ HELP")))
    return markup

# ============================================================
# START COMMAND
# ============================================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        user = register_user(user_id, username, first_name)
        
        if user.get("banned", False):
            _send_pe(message.chat.id, f"""
⭐ ═══《 🚫 ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ 》═══ ⭐

⭐ ❌ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ!

⭐ 📱 ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ

⭐ ═══════════════════════ ⭐
""")
            return
        
        # Send verification request
        markup = InlineKeyboardMarkup([
            [make_green_button("✅ SHARE VERIFICATION", callback=f"verify_{user_id}")]
        ])
        
        _send_pe(message.chat.id, f"""
⭐ ═══《 🔔 ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ 》═══ ⭐

⭐ 👤 ᴡᴇʟᴄᴏᴍᴇ {first_name}!

⭐ 📱 ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ, ᴘʟᴇᴀꜱᴇ ᴠᴇʀɪꜰʏ ʏᴏᴜʀꜱᴇʟꜰ

⭐ 🔒 ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ꜱʜᴀʀᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ

⭐ ═══════════════════════ ╭�
""", reply_markup=markup)
    except Exception as e:
        print(f"❌ Start error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("verify_"))
def verify_callback(call):
    try:
        user_id = int(call.data.split("_")[1])
        if call.from_user.id != user_id:
            _send_pe(call.message.chat.id, f"❌ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ!")
            bot.answer_callback_query(call.id)
            return
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        _send_pe(call.message.chat.id, f"""
⭐ ═══《 📱 ꜱʜᴀʀᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ 》═══ ⭐

⭐ 📱 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ:

⭐ 📞 ᴇxᴀᴍᴘʟᴇ: 9876543210

⭐ ═══════════════════════ ⭐
""")
        bot.register_next_step_handler(call.message, process_phone)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Verify callback error: {e}")

def process_phone(message):
    try:
        user_id = message.from_user.id
        phone = message.text.strip()
        
        if not phone.isdigit() or len(phone) < 10:
            _send_pe(message.chat.id, f"❌ ɪɴᴠᴀʟɪᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ! ꜱᴇɴᴅ ᴏɴʟʏ ᴅɪɢɪᴛꜱ")
            return
        
        # Save phone
        update_user(user_id, "phone", phone)
        update_user(user_id, "verified", True)
        
        user = get_user(user_id)
        
        # Notify admins
        admin_msg = f"""
⭐ ═══《 🔔 ɴᴇᴡ ᴜꜱᴇʀ ᴠᴇʀɪꜰɪᴇᴅ 》═══ ⭐

⭐ 👤 ɴᴀᴍᴇ: {user.get('name', 'Unknown')}
⭐ 🆔 ᴜꜱᴇʀ ɪᴅ: {user_id}
⭐ 👾 ᴜꜱᴇʀɴᴀᴍᴇ: @{user.get('username', 'N/A')}
⭐ 📱 ᴘʜᴏɴᴇ: {phone}

⭐ ═══════════════════════ ⭐
"""
        for admin in ADMIN_IDS:
            try:
                bot.send_message(admin, admin_msg)
            except:
                pass
        
        # Success message
        _send_pe(message.chat.id, f"""
✅ ═══《 ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ꜱᴜᴄᴄᴇꜱꜱ 》═══ ✅

⭐ ✅ ʏᴏᴜ ᴀʀᴇ ᴠᴇʀɪꜰɪᴇᴅ!

⭐ 📱 ᴘʜᴏɴᴇ: {phone}

⭐ 🎯 ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ

⭐ ═══════════════════════ ⭐
""")
        
        # Show user menu
        markup = get_user_menu()
        _send_pe(message.chat.id, f"⭐ ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ:", reply_markup=markup)
    except Exception as e:
        print(f"❌ Process phone error: {e}")

# ============================================================
# CHECK BALANCE
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("💳 CHECK BALANCE") in m.text)
def check_balance(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user or user.get("banned", False):
            _send_pe(message.chat.id, f"❌ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ!")
            return
        
        if not user.get("verified", False):
            _send_pe(message.chat.id, f"❌ ᴘʟᴇᴀꜱᴇ /start ᴀɴᴅ ᴠᴇʀɪꜰʏ ꜰɪʀꜱᴛ!")
            return
        
        balance = get_balance(user_id)
        
        # Copy-able mono amount
        copy_text = f"<code>{balance}</code>"
        
        _send_pe(message.chat.id, f"""
💳 ═══《 ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ 》═══ 💳

⭐ 👤 ᴜꜱᴇʀ: {user.get('name', 'Unknown')}
⭐ 🆔 ɪᴅ: {user_id}

⭐ 💰 ʙᴀʟᴀɴᴄᴇ:
{copy_text}

⭐ 📋 ᴛᴀᴘ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴄᴏᴘʏ

⭐ ═══════════════════════ ⭐
""", parse_mode="HTML")
    except Exception as e:
        print(f"❌ Check balance error: {e}")

# ============================================================
# ADD BALANCE (Auto Price with UPI)
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("💰 ADD BALANCE") in m.text)
def add_balance_start(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user or user.get("banned", False):
            _send_pe(message.chat.id, f"❌ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ!")
            return
        
        if not user.get("verified", False):
            _send_pe(message.chat.id, f"❌ ᴘʟᴇᴀꜱᴇ /start ᴀɴᴅ ᴠᴇʀɪꜰʏ ꜰɪʀꜱᴛ!")
            return
        
        _send_pe(message.chat.id, f"""
💰 ═══《 ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ 》═══ 💰

⭐ 📱 ᴇɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ (50-30000):

⭐ 💵 ᴇxᴀᴍᴘʟᴇ: 500

⭐ ═══════════════════════ ⭐
""")
        bot.register_next_step_handler(message, process_add_balance)
    except Exception as e:
        print(f"❌ Add balance error: {e}")

def process_add_balance(message):
    try:
        user_id = message.from_user.id
        amount_text = message.text.strip()
        
        try:
            amount = int(amount_text)
        except:
            _send_pe(message.chat.id, f"❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! ꜱᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ")
            return
        
        if amount < 50 or amount > 30000:
            _send_pe(message.chat.id, f"❌ ᴀᴍᴏᴜɴᴛ ᴍᴜꜱᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ 50-30000")
            return
        
        settings = load_settings()
        upi = settings.get("upi", "vanshx111@naviaxis")
        
        # Generate QR
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={upi}&am={amount}&cu=INR"
        
        qr_text = f"""
💰 ═══《 ᴘᴀʏᴍᴇɴᴛ 》═══ 💰

⭐ 💳 ᴜᴘɪ: {upi}
⭐ 💰 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}

⭐ 📱 ꜱᴄᴀɴ Qʀ ᴛᴏ ᴘᴀʏ

⭐ ═══════════════════════ ⭐

<code>{upi}</code>

⭐ 👨‍💻 @ɪꜰʟᴇxᴢʏᴀɴɴ
"""
        
        keyboard = [
            [make_green_button("✅ I HAVE PAID", callback=f"paid_{user_id}_{amount}")],
            [make_red_button("❌ CANCEL", callback="cancel_payment")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        try:
            bot.send_photo(message.chat.id, photo=qr_url, caption=qr_text, reply_markup=markup, parse_mode="HTML")
        except:
            _send_pe(message.chat.id, qr_text, reply_markup=markup)
    except Exception as e:
        print(f"❌ Process add balance error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("paid_"))
def handle_paid(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[1])
        amount = int(parts[2])
        
        if call.from_user.id != user_id:
            _send_pe(call.message.chat.id, f"❌ ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ!")
            bot.answer_callback_query(call.id)
            return
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        # Save pending
        pending = load_pending()
        pending[f"balance_{user_id}"] = {
            "user_id": user_id,
            "amount": amount,
            "type": "add_balance",
            "status": "pending",
            "requested": datetime.now().isoformat()
        }
        save_pending(pending)
        
        _send_pe(call.message.chat.id, f"📸 ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ!")
        bot.register_next_step_handler(call.message, receive_payment_screenshot, user_id, amount)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Handle paid error: {e}")

def receive_payment_screenshot(message, user_id, amount):
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            
            # Save screenshot
            pending = load_pending()
            key = f"balance_{user_id}"
            if key in pending:
                pending[key]["screenshot"] = file_id
                save_pending(pending)
            
            _send_pe(message.chat.id, f"✅ ʀᴇᴄᴇɪᴠᴇᴅ!\n⏳ ᴡᴀɪᴛ ꜰᴏʀ ᴀᴅᴍɪɴ ᴀᴘᴘʀᴏᴠᴀʟ")
            
            # Send to admins
            admin_text = f"""
⭐ ═══《 💰 ɴᴇᴡ ᴘᴀʏᴍᴇɴᴛ 》═══ ⭐

⭐ 👤 {message.from_user.first_name}
⭐ 🆔 {user_id}
⭐ 👾 @{message.from_user.username or 'N/A'}
⭐ 💰 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}

⭐ ═══════════════════════ ⭐
"""
            keyboard = [
                [make_green_button("✅ ᴀᴘᴘʀᴏᴠᴇ", callback=f"balance_approve_{user_id}_{amount}")],
                [make_red_button("❌ ᴅɪꜱᴀᴘᴘʀᴏᴠᴇ", callback=f"balance_disapprove_{user_id}")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            
            for admin in ADMIN_IDS:
                try:
                    bot.send_photo(admin, photo=file_id, caption=admin_text, reply_markup=markup)
                except:
                    bot.send_message(admin, admin_text, reply_markup=markup)
        else:
            _send_pe(message.chat.id, f"❌ ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ!")
    except Exception as e:
        print(f"❌ Receive screenshot error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("balance_approve_"))
def balance_approve_callback(call):
    try:
        if not is_admin(call.from_user.id):
            _send_pe(call.message.chat.id, f"❌ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
            bot.answer_callback_query(call.id)
            return
        
        parts = call.data.split("_")
        user_id = int(parts[2])
        amount = int(parts[3])
        
        # Add balance
        new_balance = add_balance(user_id, amount)
        
        # Remove from pending
        pending = load_pending()
        key = f"balance_{user_id}"
        if key in pending:
            del pending[key]
            save_pending(pending)
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        _send_pe(call.message.chat.id, f"✅ ᴀᴍᴏᴜɴᴛ ᴀᴅᴅᴇᴅ ꜰᴏʀ {user_id}!")
        
        # Notify user
        try:
            _send_pe(user_id, f"""
✅ ═══《 ʙᴀʟᴀɴᴄᴇ ᴀᴅᴅᴇᴅ 》═══ ✅

⭐ 💰 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}
⭐ 💳 ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: ʀꜱ.{new_balance}

⭐ ᴛʜᴀɴᴋ ʏᴏᴜ!

⭐ 👨‍💻 @ɪꜰʟᴇxᴢʏᴀɴɴ
""")
        except:
            pass
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Balance approve error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("balance_disapprove_"))
def balance_disapprove_callback(call):
    try:
        if not is_admin(call.from_user.id):
            _send_pe(call.message.chat.id, f"❌ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
            bot.answer_callback_query(call.id)
            return
        
        user_id = int(call.data.split("_")[2])
        
        pending = load_pending()
        key = f"balance_{user_id}"
        if key in pending:
            del pending[key]
            save_pending(pending)
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        _send_pe(call.message.chat.id, f"❌ ᴘᴀʏᴍᴇɴᴛ ʀᴇᴊᴇᴄᴛᴇᴅ ꜰᴏʀ {user_id}!")
        
        try:
            _send_pe(user_id, f"❌ ᴘᴀʏᴍᴇɴᴛ ɴᴏᴛ ᴀᴘᴘʀᴏᴠᴇᴅ.")
        except:
            pass
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Balance disapprove error: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_payment")
def cancel_payment_callback(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    _send_pe(call.message.chat.id, f"✅ ᴄᴀɴᴄᴇʟʟᴇᴅ!")
    bot.answer_callback_query(call.id)

# ============================================================
# TRANSFER BALANCE (In Groups)
# ============================================================
@bot.message_handler(commands=['transfer'])
def transfer_balance(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user or user.get("banned", False):
            _send_pe(message.chat.id, f"❌ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ!")
            return
        
        # Parse command
        parts = message.text.split()
        if len(parts) < 3:
            _send_pe(message.chat.id, f"❌ ᴜꜱᴇ: /transfer <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀɴᴀᴍᴇ>")
            return
        
        try:
            amount = int(parts[1])
        except:
            _send_pe(message.chat.id, f"❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ!")
            return
        
        target_username = parts[2].replace("@", "")
        
        if amount <= 0:
            _send_pe(message.chat.id, f"❌ ᴀᴍᴏᴜɴᴛ ᴍᴜꜱᴛ ʙᴇ ᴘᴏꜱɪᴛɪᴠᴇ!")
            return
        
        # Find target user by username
        users = load_users()
        target_user = None
        target_id = None
        
        for uid, u in users.items():
            if u.get("username", "").lower() == target_username.lower():
                target_user = u
                target_id = int(uid)
                break
        
        if not target_user:
            _send_pe(message.chat.id, f"❌ ᴜꜱᴇʀ @{target_username} ɴᴏᴛ ꜰᴏᴜɴᴅ!")
            return
        
        if target_id == user_id:
            _send_pe(message.chat.id, f"❌ ᴄᴀɴɴᴏᴛ ᴛʀᴀɴꜱꜰᴇʀ ᴛᴏ ʏᴏᴜʀꜱᴇʟꜰ!")
            return
        
        # Check sender balance
        sender_balance = get_balance(user_id)
        if sender_balance < amount:
            _send_pe(message.chat.id, f"""
❌ ═══《 ɪɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ꜰᴜɴᴅꜱ 》═══ ❌

⭐ 💰 ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ: ʀꜱ.{sender_balance}
⭐ 💸 ʀᴇQᴜɪʀᴇᴅ: ʀꜱ.{amount}

⭐ ═══════════════════════ ⭐
""")
            return
        
        # Transfer
        add_balance(user_id, -amount)
        add_balance(target_id, amount)
        
        # Notify sender
        _send_pe(message.chat.id, f"""
✅ ═══《 ᴛʀᴀɴꜱꜰᴇʀ ꜱᴜᴄᴄᴇꜱꜱ 》═══ ✅

⭐ 💸 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}
⭐ 👤 ᴛᴏ: @{target_username}

⭐ ═══════════════════════ ⭐
""")
        
        # Notify receiver
        try:
            _send_pe(target_id, f"""
💰 ═══《 ʙᴀʟᴀɴᴄᴇ ʀᴇᴄᴇɪᴠᴇᴅ 》═══ 💰

⭐ 💸 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}
⭐ 👤 ꜰʀᴏᴍ: {user.get('name', 'Unknown')} (@{user.get('username', 'N/A')})
⭐ 💰 ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: ʀꜱ.{get_balance(target_id)}

⭐ ═══════════════════════ ⭐
""")
        except:
            pass
    except Exception as e:
        print(f"❌ Transfer error: {e}")

# ============================================================
# ADMIN: ALL USERS
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("👥 ALL USERS") in m.text)
def all_users_cmd(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        users = load_users()
        balance_data = load_balance()
        
        text = f"⭐ ═══《 👥 ᴀʟʟ ᴜꜱᴇʀꜱ 》═══ ⭐\n\n"
        
        count = 0
        for uid, data in users.items():
            count += 1
            bal = balance_data.get(uid, 0)
            status = "🚫" if data.get("banned", False) else "✅"
            text += f"⭐ {count}. {data.get('name', 'Unknown')}\n"
            text += f"    🆔 <code>{uid}</code>\n"
            text += f"    💰 ʀꜱ.<code>{bal}</code> {status}\n\n"
        
        text += f"⭐ ᴛᴏᴛᴀʟ: {len(users)}"
        
        try:
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        except:
            _send_pe(message.chat.id, text)
    except Exception as e:
        print(f"❌ All users error: {e}")

# ============================================================
# ADMIN: STATS
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("📊 STATS") in m.text)
def stats_cmd(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        users = load_users()
        balance_data = load_balance()
        pending = load_pending()
        
        total_balance = sum(balance_data.values())
        banned = sum(1 for u in users.values() if u.get("banned", False))
        verified = sum(1 for u in users.values() if u.get("verified", False))
        
        _send_pe(message.chat.id, f"""
📊 ═══《 ꜱᴛᴀᴛꜱ 》═══ 📊

⭐ 👥 ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {len(users)}
⭐ ✅ ᴠᴇʀɪꜰɪᴇᴅ: {verified}
⭐ 🚫 ʙᴀɴɴᴇᴅ: {banned}
⭐ 💰 ᴛᴏᴛᴀʟ ʙᴀʟᴀɴᴄᴇ: ʀꜱ.{total_balance}
⭐ ⏳ ᴘᴇɴᴅɪɴɢ: {len(pending)}
⭐ 👑 ᴀᴅᴍɪɴꜱ: {len(ADMIN_IDS)}

⭐ ═══════════════════════ ⭐
""")
    except Exception as e:
        print(f"❌ Stats error: {e}")

# ============================================================
# ADMIN: SEND BALANCE
# ============================================================
@bot.message_handler(commands=['send'])
def send_balance_cmd(message):
    try:
        if not is_admin(message.from_user.id):
            _send_pe(message.chat.id, f"❌ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            _send_pe(message.chat.id, f"❌ ᴜꜱᴇ: /send <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀɴᴀᴍᴇ ᴏʀ ɪᴅ>")
            return
        
        try:
            amount = int(parts[1])
        except:
            _send_pe(message.chat.id, f"❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ!")
            return
        
        target = parts[2].replace("@", "")
        
        # Find user
        users = load_users()
        target_id = None
        
        if target.isdigit():
            target_id = int(target)
            if str(target_id) not in users:
                _send_pe(message.chat.id, f"❌ ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ!")
                return
        else:
            for uid, u in users.items():
                if u.get("username", "").lower() == target.lower():
                    target_id = int(uid)
                    break
            
            if not target_id:
                _send_pe(message.chat.id, f"❌ ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ!")
                return
        
        # Add balance
        new_balance = add_balance(target_id, amount)
        
        _send_pe(message.chat.id, f"""
✅ ═══《 ʙᴀʟᴀɴᴄᴇ ꜱᴇɴᴛ 》═══ ✅

⭐ 👤 ᴛᴏ: {users[str(target_id)].get('name', 'Unknown')}
⭐ 🆔 ɪᴅ: {target_id}
⭐ 💰 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}
⭐ 💳 ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: ʀꜱ.{new_balance}

⭐ ═══════════════════════ ⭐
""")
        
        # Notify user
        try:
            _send_pe(target_id, f"""
💰 ═══《 ʙᴀʟᴀɴᴄᴇ ʀᴇᴄᴇɪᴠᴇᴅ 》═══ 💰

⭐ 💸 ᴀᴍᴏᴜɴᴛ: ʀꜱ.{amount}
⭐ 👤 ꜰʀᴏᴍ: ᴀᴅᴍɪɴ
⭐ 💳 ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: ʀꜱ.{new_balance}

⭐ ═══════════════════════ ⭐
""")
        except:
            pass
    except Exception as e:
        print(f"❌ Send balance error: {e}")

# ============================================================
# ADMIN: BAN USER
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("🚫 BAN USER") in m.text)
def ban_user_start(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        _send_pe(message.chat.id, f"""
🚫 ═══《 ʙᴀɴ ᴜꜱᴇʀ 》═══ 🚫

⭐ ꜱᴇɴᴅ ᴜꜱᴇʀ ɪᴅ ᴛᴏ ʙᴀɴ:

⭐ 📱 ᴇxᴀᴍᴘʟᴇ: 123456789

⭐ ═══════════════════════ ⭐
""")
        bot.register_next_step_handler(message, process_ban_user)
    except Exception as e:
        print(f"❌ Ban user start error: {e}")

def process_ban_user(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        target = message.text.strip()
        users = load_users()
        
        if target not in users:
            _send_pe(message.chat.id, f"❌ ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ!")
            return
        
        update_user(int(target), "banned", True)
        _send_pe(message.chat.id, f"✅ ᴜꜱᴇʀ {target} ʙᴀɴɴᴇᴅ!")
    except Exception as e:
        print(f"❌ Process ban error: {e}")

# ============================================================
# ADMIN: UNBAN USER
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("✅ UNBAN USER") in m.text)
def unban_user_start(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        _send_pe(message.chat.id, f"""
✅ ═══《 ᴜɴʙᴀɴ ᴜꜱᴇʀ 》═══ ✅

⭐ ꜱᴇɴᴅ ᴜꜱᴇʀ ɪᴅ ᴛᴏ ᴜɴʙᴀɴ:

⭐ 📱 ᴇxᴀᴍᴘʟᴇ: 123456789

⭐ ═══════════════════════ ⭐
""")
        bot.register_next_step_handler(message, process_unban_user)
    except Exception as e:
        print(f"❌ Unban user start error: {e}")

def process_unban_user(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        target = message.text.strip()
        users = load_users()
        
        if target not in users:
            _send_pe(message.chat.id, f"❌ ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ!")
            return
        
        update_user(int(target), "banned", False)
        _send_pe(message.chat.id, f"✅ ᴜꜱᴇʀ {target} ᴜɴʙᴀɴɴᴇᴅ!")
    except Exception as e:
        print(f"❌ Process unban error: {e}")

# ============================================================
# ADMIN: SET UPI
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("⚙️ SET UPI") in m.text)
def set_upi_start(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        settings = load_settings()
        current = settings.get("upi", "vanshx111@naviaxis")
        
        _send_pe(message.chat.id, f"""
⚙️ ═══《 ꜱᴇᴛ ᴜᴘɪ 》═══ ⚙️

⭐ ᴄᴜʀʀᴇɴᴛ: {current}

⭐ ꜱᴇɴᴅ ɴᴇᴡ ᴜᴘɪ ɪᴅ:

⭐ 📱 ᴇxᴀᴍᴘʟᴇ: yourupi@paytm

⭐ ═══════════════════════ ⭐
""")
        bot.register_next_step_handler(message, process_set_upi)
    except Exception as e:
        print(f"❌ Set UPI start error: {e}")

def process_set_upi(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        upi = message.text.strip()
        settings = load_settings()
        settings["upi"] = upi
        save_settings(settings)
        
        _send_pe(message.chat.id, f"✅ ᴜᴘɪ ꜱᴇᴛ ᴛᴏ: {upi}")
    except Exception as e:
        print(f"❌ Process set UPI error: {e}")

# ============================================================
# ADMIN: BROADCAST
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("📢 BROADCAST") in m.text)
def broadcast_start(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        _send_pe(message.chat.id, f"""
📢 ═══《 ʙʀᴏᴀᴅᴄᴀꜱᴛ 》═══ 📢

⭐ ꜱᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ:

⭐ ═══════════════════════ ⭐
""")
        bot.register_next_step_handler(message, process_broadcast)
    except Exception as e:
        print(f"❌ Broadcast start error: {e}")

def process_broadcast(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        msg = message.text.strip()
        users = load_users()
        sent = 0
        failed = 0
        
        _send_pe(message.chat.id, f"⏳ ꜱᴇɴᴅɪɴɢ ᴛᴏ {len(users)} ᴜꜱᴇʀꜱ...")
        
        for user_id in users.keys():
            try:
                _send_pe(int(user_id), f"📢 {msg}")
                sent += 1
                time.sleep(0.05)
            except:
                failed += 1
        
        _send_pe(message.chat.id, f"✅ ᴄᴏᴍᴘʟᴇᴛᴇ!\n⭐ ꜱᴇɴᴛ: {sent}\n❌ ꜰᴀɪʟᴇᴅ: {failed}")
    except Exception as e:
        print(f"❌ Process broadcast error: {e}")

# ============================================================
# SUPPORT
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("🆘 SUPPORT") in m.text)
def support_cmd(message):
    try:
        settings = load_settings()
        support = settings.get("support", "@iflexzyann")
        
        _send_pe(message.chat.id, f"""
🆘 ═══《 ꜱᴜᴘᴘᴏʀᴛ 》═══ 🆘

⭐ 👨‍💻 {support}

⭐ ꜰᴏʀ ᴀɴʏ ɪꜱꜱᴜᴇ:
⭐ 📱 {support}

⭐ ═══════════════════════ ⭐
""", reply_markup=InlineKeyboardMarkup([
            [make_green_button("CONTACT SUPPORT", url=f"https://t.me/{support.replace('@', '')}")]
        ]))
    except Exception as e:
        print(f"❌ Support error: {e}")

# ============================================================
# HELP
# ============================================================
@bot.message_handler(func=lambda m: m.text and stylish_text("ℹ️ HELP") in m.text)
def help_cmd(message):
    try:
        user_id = message.from_user.id
        
        if is_admin(user_id):
            _send_pe(message.chat.id, f"""
ℹ️ ═══《 ᴀᴅᴍɪɴ ʜᴇʟᴘ 》═══ ℹ️

⭐ /send <ᴀᴍᴛ> <ɪᴅ/@ᴜꜱᴇʀɴᴀᴍᴇ>
⭐ /broadcast - ꜱᴇɴᴅ ᴍꜱɢ ᴛᴏ ᴀʟʟ
⭐ /users - ᴀʟʟ ᴜꜱᴇʀꜱ ᴡɪᴛʜ ʙᴀʟᴀɴᴄᴇ

⭐ ═══════════════════════ ⭐
""", reply_markup=get_admin_menu())
        else:
            _send_pe(message.chat.id, f"""
ℹ️ ═══《 ʜᴇʟᴘ 》═══ ℹ️

⭐ 💰 ADD BALANCE - ᴀᴅᴅ ᴍᴏɴᴇʏ
⭐ 💳 CHECK BALANCE - ᴠɪᴇᴡ ʙᴀʟᴀɴᴄᴇ
⭐ 💸 TRANSFER BALANCE - ꜱᴇɴᴅ ᴍᴏɴᴇʏ
⭐ /transfer <ᴀᴍᴛ> @<ᴜꜱᴇʀɴᴀᴍᴇ>

⭐ ═══════════════════════ ⭐
""", reply_markup=get_user_menu())
    except Exception as e:
        print(f"❌ Help error: {e}")

# ============================================================
# FLASK WEBHOOK
# ============================================================
@app.route('/', methods=['GET'])
def index():
    return "✅ Balance Bot is running!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
    except Exception as e:
        print(f"❌ Webhook error: {e}")
    return '', 403

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("✅ Bot starting...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"👥 Users: {len(load_users())}")
    print(f"👑 Admins: {len(ADMIN_IDS)}")
    
    try:
        bot.remove_webhook()
        print("✅ Webhook removed!")
    except Exception as e:
        print(f"⚠️ {e}")
    
    try:
        hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if hostname:
            webhook_url = f"https://{hostname}/{BOT_TOKEN}"
            bot.set_webhook(url=webhook_url)
            print(f"✅ Webhook set: {webhook_url}")
        else:
            print("⚠️ No hostname, using polling")
            bot.infinity_polling()
            exit()
    except Exception as e:
        print(f"⚠️ {e}, falling back to polling")
        bot.infinity_polling()
        exit()
    
    app.run(host='0.0.0.0', port=PORT)

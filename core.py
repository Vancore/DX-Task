from data import db
from telebot import types
import os

def check_str(txt):
    if txt == "":
        return False
    for char in "<>&":
        if char in txt:
            return False
            
    return True

def welcome(uid):
    return ("<b>DX Task</b>\n"
            "Everything in its place.\n\n"
            "Simple, focused, and designed to keep your mind clear.\n"
            "To begin, create your first collection:\n\n"
            "/new — Create new list\n"
            "/help — Command guide")

def help_text():
    return (
        "<b>DX Task — Guide</b> 🛠\n\n"
        "<b>Collections:</b>\n"
        "/new — Create new list\n"
        "/lists — View all collections\n"
        "/edit — Switch active list\n"
        "/rem — Delete collection\n\n"
        "<b>Tasks:</b>\n"
        "/list — Show current tasks\n"
        "/add — Add new task\n"
        "/done — Mark as completed\n"
        "/del — Delete task\n\n"
        "<b>Quick Add:</b>\n"
        "<i>In private chats, you can just type any text without /add to save a task.</i>"
    )

def show_list(lid):
    name = db.get_list_title(lid)
    text = f"<b>{name}</b>\n"
    tasks = db.get_tasks(lid)
    if tasks == []:
        text += "Just type to add a task."
    i = 1
    for id, txt, done in tasks:
        if done == 0:
            text += "🔘 "
        else: text += "✅ "
        text += f"{i}.{txt}\n"
        i += 1
    return text


def create_list(uid, name):
    name = name.strip()
    if db.count_lists(uid) >= 3 and not db.is_premium(uid):
        return ("<b>Collection Limit Reached.</b>\n\n"
                "To keep your focus sharp, the free version is limited to 3 collections.\n\n"
                "Upgrade to <b>DX Pro</b> for more, or use /rem to manage your lists."
            )
    if db.count_lists(uid) >= 30:
        return ("<b>Maximum Limit Reached.</b>\n\n"
                "DX Task supports up to 30 active collections.\n"
                "Please use /rem to free up some space."
            )
    if len(name) > 30:
        return "<b>Name is too long.</b>\nMax 30 characters."
    if not check_str(name):
        return ("<b>Invalid name.</b>\n"
            "Please avoid using symbols like &lt;, &gt;, or &amp;.")
    lid = db.add_list(uid, name)
    db.set_active_list(uid, lid)
    return show_list(lid)

def add_task(uid, text):
    text = text.strip()
    lid = db.get_active_list(uid)
    if lid == None:
        return ("<b>No active list.</b>\n"
            "Please create a new collection or select an existing one to continue.\n\n"
            "/new — Create new\n"
            "/edit — Select existing")
    if db.count_tasks(lid) >= 15 and not db.is_premium(uid):
        return ("<b>Focus Limit Reached.</b>\n\n"
                "Free lists are limited to 15 tasks to keep your day manageable.\n\n"
                "Use /del to remove tasks, or upgrade to <b>DX Pro</b> for 30 slots.")
    if db.count_tasks(lid) >= 30:
        return ("<b>Maximum Capacity.</b>\n\n"
                "You've reached the limit of 30 tasks.\n\n"
                "Use /del to free up some space and stay productive.")
    if len(text) > 100:
            return "<b>Task is too long.</b>\nKeep it under 100 characters."
    if not check_str(text):
        return ("<b>Invalid characters.</b>\n"
                "Please avoid using &lt;, &gt;, or &amp;.")
    db.add_task(lid, text)
    return show_list(lid)


def get_cur_list(uid):
    lid = db.get_active_list(uid)
    if lid == None:
        return ("<b>No active list.</b>\n"
            "Please create a new collection or select an existing one to continue.\n\n"
            "/new — Create new\n"
            "/edit — Select existing")
    return show_list(lid)

def get_all(uid):
    if db.count_lists(uid) == 0:
        return ("<b>You have no collections yet.</b>\nUse /new to create one.")
    text = "<b>YOUR COLLECTIONS</b>\n\n"
    for id, name in db.get_all_list(uid):
        text += f"• {name}\n"
    return text

#UI
def get_edit_ui(uid):
    lists = db.get_all_list(uid)
    if not lists:
        return ("<b>No collections found.</b>\nUse /new to create one.", None)
    markup = types.InlineKeyboardMarkup()
    for lid, title in lists:
        btn = types.InlineKeyboardButton(text=title, callback_data=f"dx_s_{lid}")
        markup.add(btn)
    markup.add(types.InlineKeyboardButton(text="⬅️ Back", callback_data="dx_main"))
    return "<b>Select active collection:</b>", markup

def get_delete_ui(uid):
    lid = db.get_active_list(uid)
    if lid == None:
        return ("<b>No active list.</b>\nCreate or select one first.", None)
    tasks = db.get_tasks(lid)
    if not tasks:
        return ("<b>List is empty.</b>\nNothing to delete.", None)
    markup = types.InlineKeyboardMarkup()
    for tid, name, done in tasks:
        short_txt = name[:20] + "..." if len(name) > 20 else name
        btn = types.InlineKeyboardButton(text=f"{short_txt}", callback_data=f"dx_d_{tid}")
        markup.add(btn)
    markup.add(types.InlineKeyboardButton(text="⬅️ Back", callback_data="dx_main"))
    return "<b>Select a task to delete:</b>", markup


def get_done_ui(uid):
    lid = db.get_active_list(uid)
    if lid == None:
        return ("<b>No active list.</b>\nCreate or select one first.", None)
    tasks = db.get_tasks(lid)
    if not tasks:
        return ("<b>List is empty.</b>\n", None)
    markup = types.InlineKeyboardMarkup()
    for tid, name, done in tasks:
        short_txt = name[:20] + "..." if len(name) > 20 else name
        btn = types.InlineKeyboardButton(text=f"{'✅' if done else ''} {name}", callback_data=f"dx_v_{tid}")
        markup.add(btn)
    markup.add(types.InlineKeyboardButton(text="⬅️ Back", callback_data="dx_main"))
    return "<b>Mark tasks as done:</b>", markup


def get_rem_ui(uid):
    lists = db.get_all_list(uid)
    if not lists:
        return "<b>No collections to remove.</b>", None
    markup = types.InlineKeyboardMarkup()
    for lid, title in lists:
        btn = types.InlineKeyboardButton(text=f"❗Delete: {title}", callback_data=f"dx_r_{lid}")
        markup.add(btn)
    markup.add(types.InlineKeyboardButton(text="⬅️ Back", callback_data="dx_main"))
    return ("⚠️ <b>Select a collection to DELETE:</b>\n"
        "<i>This action will permanently remove all tasks in the list.</i>", 
        markup)


def get_donate_ui():
    text = (
        "<b>Upgrade to DX Pro</b> ⚡\n\n"
        "Unlock the full potential of your task management:\n"
        "• Up to <b>30 collections</b> (instead of 3)\n"
        "• Up to <b>30 tasks</b> per list (instead of 15)\n"
        "• Support independent development\n\n"
        "<i>One-time payment: 50 Stars</i>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⭐️ Activate DX Pro (50 Stars)", callback_data="dx_pay_50"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="dx_main"))
    return text, markup


#ADMIN
def get_admin_stats():
    total = db.count_users()
    premiums = db.get_premium_users()
    file_size = os.path.getsize("data.db") / 1024
    return (
        "📊 <b>DX SYSTEM MONITOR</b>\n"
        "————————————————\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"⭐ Premium: <b>{premiums}</b>\n"
        f"💾 DB Size: <b>{file_size:.2f} KB</b>\n"
        "————————————————\n"
        "<i>Status: Operational</i>"
    )
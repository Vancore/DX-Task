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
    return (
        "<b>DX Task</b>\n"
        "Everything in its place.\n\n"
        "Simple, focused, and designed to keep your mind clear.\n"
        "To begin, create your first collection."
    )

def help_text():
    return (
        "<b>DX Task — System Protocol</b> 🛠\n"
        "<i>Everything in its place.</i>\n\n"
        
        "<b>📂 Collections</b>\n"
        "/new — Create a new list\n"
        "/lists — View all your collections\n"
        "/edit — Switch the active list\n"
        "/rem — Permanently delete a list\n\n"
        
        "<b>📝 Tasks</b>\n"
        "/list — Show tasks in the active list\n"
        "/add — Add a task manually\n"
        "/done — Mark tasks as completed\n"
        "/del — Remove tasks from the list\n\n"
        
        "<b>📱 Private Chat</b>\n"
        "/on — Enable Control Panel\n"
        "/off — Disable Control Panel\n"
        "<i>Quick Add: Just type and send any text.</i>\n\n"
        
        "<b>⚙️ System</b>\n"
        "/donate — Upgrade to DX Pro\n"
        "/help — Show this protocol"
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
        return (
            "<b>Collection Limit Reached.</b>\n\n"
            "To maintain absolute focus, the standard core is limited to 3 collections.\n\n"
            "Expand your system's capacity with <b>DX Pro</b> or remove an existing collection to continue."
            )
    if db.count_lists(uid) >= 30:
        return (
            "<b>Maximum Capacity.</b>\n\n"
            "The system is optimized for up to 30 active collections.\n"
            "Please remove an existing collection to free up space."
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
        return (
            "<b>No Active Collection.</b>\n"
            "Please create a new list or select an existing one to continue."
            )
    if db.count_tasks(lid) >= 15 and not db.is_premium(uid):
        return (
            "<b>Focus Limit Reached.</b>\n\n"
            "Standard collections are limited to 15 tasks to maintain absolute clarity.\n\n"
            "Upgrade to <b>DX Pro</b> for expanded capacity or remove existing tasks to free up space."
        )
    if db.count_tasks(lid) >= 30:
        return (
            "<b>Maximum Capacity.</b>\n\n"
            "This collection has reached its 30-task limit.\n"
            "Please remove existing entries to free up space and maintain focus."
        )
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
        return (
            "<b>No Active Collection.</b>\n"
            "Please create a new list or select an existing one to continue."
        )
    return show_list(lid)

def get_all(uid):
    if db.count_lists(uid) == 0:
        return ("<b>No Collections Found.</b>\nPlease create a new collection to begin.")
    text = "<b>YOUR COLLECTIONS</b>\n\n"
    for id, name in db.get_all_list(uid):
        text += f"• {name}\n"
    return text

#UI
def get_edit_ui(uid):
    lists = db.get_all_list(uid)
    if not lists:
        return ("<b>No Collections Found.</b>\nPlease create a new collection to begin.", None)
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
        "<b>DX Pro — The Professional Standard</b> ⚡\n\n"
        "Elevate your system to its full architectural capacity. "
        "Unlock the power of professional task management:\n\n"
        "• <b>30 Collections</b> — Build your empire.\n"
        "• <b>30 Tasks</b> per list — Master every detail.\n"
        "• Support the evolution of DX Task.\n\n"
        "<i>Lifetime Activation: 50 Stars</i>"
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
import telebot
from config import TOKEN, ADMIN_ID
from data import db
import core
from telebot.apihelper import ApiTelegramException
import time
import threading
from telebot import types

bot = telebot.TeleBot(TOKEN)

user_locks = {}
flood_lock = threading.Lock()

def is_flooding(uid):
    with flood_lock:
        now = time.time()
        if uid in user_locks and now - user_locks[uid] < 0.7:
            return True
        user_locks[uid] = now
        if len(user_locks) > 2000:
            expired = [k for k, v in user_locks.items() if now - v > 60]
            for k in expired: del user_locks[k]
        return False

def send_edit(uid, text, reply_markup=None, send_new=False):
    last_id = db.get_last_msg(uid)
    if last_id and not send_new:
        try:
            return bot.edit_message_text(chat_id=uid, message_id=last_id,text=text,reply_markup=reply_markup,parse_mode="HTML")
        except:
            pass
    msg = bot.send_message(uid, text, reply_markup=reply_markup, parse_mode="HTML")
    db.update_last_msg(uid, msg.message_id)
    return msg

def delete_msg(uid, message_id):
    try:
        bot.delete_message(uid, message_id)
    except ApiTelegramException:
        pass

def safe_answer(call_id, text=None):
    try:
        bot.answer_callback_query(call_id, text)
    except ApiTelegramException as e:
        if "query is too old" in e.description:
            pass
        else:
            print(f"{e.description}")


def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="DX Task System...")
    markup.row(
        types.KeyboardButton('➕ New List'), 
        types.KeyboardButton('✅ Done'), 
        types.KeyboardButton('🗑 Delete')
    )
    markup.row(
        types.KeyboardButton('🔄 Switch'), 
        types.KeyboardButton('🗂 Collections'), 
        types.KeyboardButton('📋 Tasks')
    )
    markup.row(
        types.KeyboardButton('⚠️ Wipe'), 
        types.KeyboardButton('❓ Guide'), 
        types.KeyboardButton('⭐️ DX Pro')
    )
    return markup


@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = core.welcome(uid)
    if message.chat.type != 'private':
            bot.send_message(uid, text, parse_mode="HTML")
            return
    menu = get_main_menu()
    bot.send_message(uid, text, reply_markup=menu, parse_mode="HTML")

@bot.message_handler(commands=['new'])
def new_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = "Name your new list:"
    send_edit(uid, text)
    bot.register_next_step_handler_by_chat_id(uid, reg_list)
def reg_list(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    if not message.text: return
    if is_flooding(uid): return
    name = message.text
    text = core.create_list(uid, name)
    msg = send_edit(uid, text)


@bot.message_handler(commands=['add'])
def add_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = "Type your new task:"
    send_edit(uid, text)
    bot.register_next_step_handler_by_chat_id(uid, add_task)
def add_task(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    if not message.text: return
    if is_flooding(uid): return
    text = core.add_task(uid, message.text)
    send_edit(uid, text)

@bot.message_handler(commands=['list'])
def list_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text = core.get_cur_list(uid)
    is_group = message.chat.type != 'private'
    old_mid = db.get_last_msg(uid)
    if old_mid and is_group:
        delete_msg(uid, old_mid)
    send_edit(uid, text, send_new=is_group)

@bot.message_handler(commands=['lists'])
def lists_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text = core.get_all(uid)
    is_group = message.chat.type != 'private'
    old_mid = db.get_last_msg(uid)
    if old_mid and is_group:
        delete_msg(uid, old_mid)
    send_edit(uid, text, send_new=is_group)

@bot.message_handler(commands=['edit'])
def edit_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text, markup = core.get_edit_ui(uid)
    is_group = message.chat.type != 'private'
    old_mid = db.get_last_msg(uid)
    if old_mid and is_group:
        delete_msg(uid, old_mid)
    send_edit(uid, text, reply_markup=markup, send_new=is_group)

@bot.message_handler(commands=['del'])
def del_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text, markup = core.get_delete_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['done'])
def done_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text, markup = core.get_done_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['rem'])
def rem_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text, markup = core.get_rem_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text = core.help_text()
    send_edit(uid, text)

@bot.message_handler(commands=['off'])
def menu_off(message):
    if message.chat.type != 'private':
            return
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    markup = types.ReplyKeyboardRemove()
    text = "<b>Interface Hidden.</b>\nUse /on to restore the Control Panel."
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['on'])
def menu_on(message):
    if message.chat.type != 'private':
            return
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    markup = get_main_menu()
    text = "<b>Interface Restored.</b>\nSystem is ready."
    bot.send_message(uid, text, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(commands=['donate'])
def donate_handler(message):
    uid = message.chat.id
    if is_flooding(uid): return
    delete_msg(uid, message.message_id)
    text, markup = core.get_donate_ui()
    send_edit(uid, text, reply_markup=markup)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    uid = message.chat.id
    db.set_pro(uid)
    delete_msg(uid, message.message_id)
    text = (
        "<b>DX Pro Activated!</b> 🏆\n\n"
        "Your system has been upgraded. All limits are now expanded.\n"
        "Thank you for supporting the core."
    )
    send_edit(uid, text)

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    uid = message.chat.id
    if uid != ADMIN_ID:
        return
    delete_msg(uid, message.message_id)
    text = core.get_admin_stats()
    send_edit(uid, text)

@bot.message_handler(commands=['get'])
def admin_give_pro(message):
    uid = message.chat.id
    if uid != ADMIN_ID:
        return
    delete_msg(uid, message.message_id)
    try:
        target_id = int(message.text.split()[1])
        db.set_pro(target_id)
        bot.send_message(uid, f"✅ <b>DX Pro</b> activated for ID: <code>{target_id}</code>", parse_mode="HTML")
        bot.send_message(target_id, "🚀 <b>DX Pro Activated!</b>\nYour account has been upgraded by administrator.", parse_mode="HTML")
    except (IndexError, ValueError):
        bot.send_message(uid, "❌ Usage: <code>/get &lt;user_id&gt;</code>", parse_mode="HTML")


@bot.message_handler(func=lambda message: True)
def all_handler(message):
    if message.chat.type != 'private':
        return
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    if not message.text: return
    text = message.text
    if text == '📋 Tasks': return list_handler(message)
    if text == '✅ Done': return done_handler(message)
    if text == '🗑 Delete': return del_handler(message)
    if text == '➕ New List': return new_handler(message)
    if text == '🗂 Collections': return lists_handler(message)
    if text == '🔄 Switch': return edit_handler(message)
    if text == '⚠️ Wipe': return rem_handler(message)
    if text == '❓ Guide': return help_handler(message)
    if text == '⭐️ DX Pro':  return donate_handler(message)
    if is_flooding(uid): return
    db.add_user(uid)
    text = core.add_task(uid, message.text)
    send_edit(uid, text)


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.message.chat.id
    if is_flooding(uid):
        safe_answer(call.id, "Too fast! Please wait a moment.")
        return
    data = call.data
    if data.startswith("dx_s_"):
        list_id = int(data.split("_")[2])
        db.set_active_list(uid, list_id)
        safe_answer(call.id, "Active list updated.")
        text = core.show_list(list_id)
        send_edit(uid, text)

    elif data == "dx_main":
        safe_answer(call.id)
        text = core.get_cur_list(uid)
        send_edit(uid, text)

    elif data.startswith("dx_d_"):
        task_id = int(data.split("_")[2])
        db.delete_task(task_id)
        safe_answer(call.id, "Task removed.")
        text, markup = core.get_delete_ui(uid)
        send_edit(uid, text, reply_markup=markup)

    elif data.startswith("dx_v_"):
        task_id = int(data.split("_")[2])
        done = db.done_task(task_id)
        safe_answer(call.id, "Task completed! ✅" if done else "Task restored.")
        text, markup = core.get_done_ui(uid)
        send_edit(uid, text, reply_markup=markup)

    elif data.startswith("dx_r_"):
        list_id = int(data.split("_")[2])
        db.rem_list(list_id)
        safe_answer(call.id, "Collection destroyed.")
        text, markup = core.get_rem_ui(uid)
        send_edit(uid, text, reply_markup=markup)

    elif data.startswith("dx_pay_"):
        amount = int(data.split("_")[2])
        safe_answer(call.id, "Generating invoice...")
        bot.send_invoice(
            chat_id=uid,
            title="Support DX Task",
            description=f"Donation of {amount} Stars",
            invoice_payload=f"donate_{amount}",
            provider_token="",
            currency="XTR",
            prices=[telebot.types.LabeledPrice(label="Stars", amount=amount)]
        )

bot.infinity_polling()

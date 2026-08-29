import telebot
from config import TOKEN, ADMIN_ID
from data import db
import core
from telebot.apihelper import ApiTelegramException

bot = telebot.TeleBot(TOKEN)

def send_edit(uid, text, reply_markup=None):
    last_id = db.get_last_msg(uid)
    if last_id:
        try:
            return bot.edit_message_text(chat_id=uid, message_id=last_id,text=text,reply_markup=reply_markup,parse_mode="HTML")
        except ApiTelegramException as e:
            if "message is not modified" in e.description:
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


@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.chat.id
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = core.welcome(uid)
    send_edit(uid, text)

@bot.message_handler(commands=['new'])
def new_handler(message):
    uid = message.chat.id
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = "Name your new list:"
    send_edit(uid, text)
    bot.register_next_step_handler_by_chat_id(uid, reg_list)
def reg_list(message):
    uid = message.chat.id
    name = message.text
    text = core.create_list(uid, name)
    msg = send_edit(uid, text)
    delete_msg(uid, message.message_id)


@bot.message_handler(commands=['add'])
def add_handler(message):
    uid = message.chat.id
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = "Type your new task:"
    send_edit(uid, text)
    bot.register_next_step_handler_by_chat_id(uid, add_task)
def add_task(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text = core.add_task(uid, message.text)
    send_edit(uid, text)

@bot.message_handler(commands=['list'])
def list_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text = core.get_cur_list(uid)
    send_edit(uid, text)

@bot.message_handler(commands=['lists'])
def lists_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text = core.get_all(uid)
    send_edit(uid, text)

@bot.message_handler(commands=['edit'])
def edit_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text, markup = core.get_edit_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['del'])
def del_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text, markup = core.get_delete_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['done'])
def done_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text, markup = core.get_done_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['rem'])
def rem_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text, markup = core.get_rem_ui(uid)
    send_edit(uid, text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_handler(message):
    uid = message.chat.id
    delete_msg(uid, message.message_id)
    text = core.help_text()
    send_edit(uid, text)


@bot.message_handler(commands=['donate'])
def donate_handler(message):
    uid = message.chat.id
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
    db.add_user(uid)
    delete_msg(uid, message.message_id)
    text = core.add_task(uid, message.text)
    send_edit(uid, text)


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.message.chat.id
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
        if isinstance(text, tuple):
            send_edit(uid, text[0], reply_markup=text[1])
        else:
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

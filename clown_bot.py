import logging
import asyncio
import sqlite3 as sq
import time
from telegram import Update, ReactionTypeEmoji, Message
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, MessageReactionHandler, CallbackContext

ADMIN_ID = #число, user_id админа. Пользователь с таким user_id сможет пользоваться командами ...base_..., protect 
TOKEN = #строка, токен вашего бота


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)



def db_start():
    global db, cur 
    db = sq.connect('./botdata.db')
    cur = db.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY, name TEXT, cursed INTEGER, store INTEGER, revenge INTEGER, protect INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS chats(chat_id TEXT PRIMARY KEY, name TEXT, store INTEGER)")
    # cur.execute("CREATE TABLE IF NOT EXISTS user_add_request(number INTEGER PRIMARY KEY user_id TEXT name TEXT cursed INTEGER store INTEGER revenge INTEGER)")
    db.commit()


def get_string(table_name, coloumn, key):
    return cur.execute("SELECT * FROM '{table_name}' WHERE {coloumn} = {key}".format(table_name=table_name, coloumn=coloumn, key=key)).fetchone()

def del_string(table_name, coloumn, key):
    cur.execute("DELETE FROM '{table_name}' WHERE {coloumn} = {key}".format(table_name=table_name, coloumn=coloumn, key=key))
    db.commit()

def add_string(table_name, n_vals, values):
    cur.execute("INSERT INTO '{table_name}' VALUES({vals})".format(table_name=table_name, vals=("?, "*(n_vals - 1) + "?")), values)
    db.commit()

async def db_upd_user(user_id, name, cursed, store, revenge, protect):
    usr = cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id, )).fetchone()
    if usr:
        cur.execute("UPDATE users SET name=?, cursed=?, store=?, revenge=?, protect = ? WHERE user_id = ?", (name, cursed, store, revenge, protect, user_id))
        if store:
            cur.execute("CREATE TABLE IF NOT EXISTS '{user_id}'(number INTEGER PRIMARY KEY, message_id TEXT, chat_id TEXT, text TEXT, clown INTEGER, clown_from_prot INTEGER)".format(user_id=user_id))
        else:
            cur.execute("DROP TABLE IF EXISTS '{user_id}'".format(user_id=user_id))
    else:
        cur.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?)", (user_id, name, cursed, store, revenge, protect))
        if (store):
            cur.execute("CREATE TABLE IF NOT EXISTS '{user_id}'(number INTEGER PRIMARY KEY, message_id TEXT, chat_id TEXT, text TEXT, clown INTEGER, clown_from_prot INTEGER)".format(user_id=user_id))
    db.commit()


async def add_message_user(message, flag, store):
    max_num = cur.execute("SELECT MAX(number) FROM '{user_id}'".format(user_id=message.from_user.id)).fetchone()[0]
    min_num = cur.execute("SELECT MIN(number) FROM '{user_id}'".format(user_id=message.from_user.id)).fetchone()[0]
    if not max_num:
        max_num = 0
        min_num = 0
    cur.execute("INSERT INTO '{user_id}' VALUES(?, ?, ?, ?, ?, 0)".format(user_id=message.from_user.id), (max_num + 1, message.message_id, message.chat.id, message.text, flag))
    db.commit()
    print(min_num, max_num)
    while max_num - min_num >= store - 1:
        cur.execute("DELETE FROM '{user_id}' WHERE number=? ".format(user_id=message.from_user.id), (min_num, ))
        db.commit()
        min_num = cur.execute("SELECT MIN(number) FROM '{user_id}'".format(user_id=message.from_user.id)).fetchone()[0]
    if min_num > 100000:
        min_num_buff = min_num
        for i in range(store):
            print(message.from_user.id, i, i + min_num_buff)
            cur.execute("UPDATE '{user_id}' SET number =? WHERE number=?".format(user_id=message.from_user.id), (i,  min_num_buff + i))
            db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🤡")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Clown-bot - самый продвинутый клоун-бот в telegram! (наверное) \n\n\n У бота 7 команд:\n\n /clown - ставит клоуна на сообщение, ответом на которое она отправлена. С этой команды и началось создание бота \n\n /unclown - напротив, убирает клоуна с сообщения, ответом на которое она отправлена \n\n /protect - делает пользователя, в ответ на сообщение которого отправлена, Защищенным. Только Защищенные пользователи могут использовать эту и последующие команды. Более того, если Незащищенный пользователь поставил клоуна на сообщение Защищенного пользователя (такая ситуация называется борзостью), то он сам получит клоуна от бота на свое последнее сообщение (сообщения хранятся в базе бота, и если он не помнит ни одного сообщения от оборзевшего Незащищенного пользователя, то клоун прилетит на его следующее сообщение) \n\n /unprotect - делает пользователя, в ответ на сообщение которого отправлена, Незащищенным. Если пользователя ни разу не сделали Защищенным или Незащищенным, то он не будет ни тем, ни другим (пользоваться командами кроме первых двух не сможет, клоуна в случае борзости получит только если бот уже помнит одно из его последних сообщений) \n\n /curse - накладывает проклятие клоуна на пользователя, в ответ на сообщение которого была отправлена. Бот поставит клоуна на все сообщения проклятого пользователя, которые помнит, и будет ставит клоунов на все его новые сообщения, пока проклятие не снимут \n\n /revenge - после этой команды в том же самом сообщении надо написать число. Бот поставит это число клоунов на свободные от его клоунов сообщения (которые он помнит) пользователя, в ответ на сообщение которого отправлена команда. Если сообщений в памяти бота не хватит, оставлееся число клоунов придет на будущие сообщения этого пользователя. \n\n /amnesty - убирает клоунов со всех сообщений (которые помнит бот) от пользователя, в ответ на сообщение которого отправлена, снимает проклятия и отменяет месть \n\n Если написать команду без ответа на сообщение или не имея на нее прав, то само сообщение с командой получает клоуна \n\n\n  P.S. На баги не быковать, бот пока сырой")
    await db_upd_chat(update.effective_chat.id, update.effective_chat.first_name, 500)


async def db_upd_chat(chat_id, name, store):
    print(chat_id, name, store)
    cht = get_string("chats", "chat_id", chat_id)
    if cht:
        cur.execute("UPDATE chats SET name=?, store=? WHERE chat_id = ?", (name, store, chat_id))
        if store:
            cur.execute("CREATE TABLE IF NOT EXISTS 'c{chat_id}'(number INTEGER PRIMARY KEY, message_id TEXT, user_id TEXT, text TEXT, clown INTEGER, clown_from_prot INTEGER)".format(chat_id=chat_id))
        else:
            cur.execute("DROP TABLE IF EXISTS 'c{chat_id}'".format(chat_id=chat_id))
    else:
        add_string("chats", 3, (chat_id, name, store))
        if (store):
            cur.execute("CREATE TABLE IF NOT EXISTS 'c{chat_id}'(number INTEGER PRIMARY KEY, message_id TEXT, user_id TEXT, text TEXT, clown INTEGER, clown_from_prot INTEGER)".format(chat_id=chat_id))
    db.commit()

async def add_message_chat(message, flag, store):
    max_num = cur.execute("SELECT MAX(number) FROM 'c{chat_id}'".format(chat_id=message.chat.id)).fetchone()[0]
    min_num = cur.execute("SELECT MIN(number) FROM 'c{chat_id}'".format(chat_id=message.chat.id)).fetchone()[0]
    if not max_num:
        max_num = 0
        min_num = 0
    cur.execute("INSERT INTO 'c{chat_id}' VALUES(?, ?, ?, ?, ?, 0)".format(chat_id=message.chat.id), (max_num + 1, message.message_id, message.from_user.id, message.text, flag))
    db.commit()
    print(min_num, max_num)
    while max_num - min_num >= store - 1:
        cur.execute("DELETE FROM 'c{chat_id}' WHERE number=? ".format(chat_id = message.chat.id), (min_num, ))
        db.commit()
        min_num = cur.execute("SELECT MIN(number) FROM 'c{chat_id}'".format(chat_id=message.chat.id)).fetchone()[0]
    if min_num > 100000:
        min_num_buff = min_num
        for i in range(store):
            print(message.from_user.id, i, i + min_num_buff)
            cur.execute("UPDATE 'c{chat_id}' SET number =? WHERE number=?".format(chat_id=message.chat.id), (i,  min_num_buff + i))
            db.commit()



async def messageh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print(update.message)
    usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.from_user.id)).fetchone()
    cht = get_string("chats", "chat_id", update.message.chat.id)
    flag = 0
    print(cht)
    print(usr)
    if usr:
        if usr[2]:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
            flag = 1
        if usr[4] and (not flag):
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
            cur.execute("UPDATE users SET revenge = (revenge - 1) WHERE user_id = ?", (user.id, ))
            db.commit()
        if usr[3]:
            await add_message_user(update.message, flag, usr[3])
        else:
            cur.execute("DROP TABLE IF EXISTS '{user_id}'".format(user_id=update.message.from_user.id))
            db.commit()
    if cht:
        if cht[2]:
            await add_message_chat(update.message, flag, cht[2])
        else:
            cur.execute("DROP TABLE IF EXISTS 'c{chat_id}'".format(chat_id=update.message.chat.id))


   #await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def do_revenge(user, context):
    max_num = cur.execute("SELECT MAX(number) FROM '{user_id}'".format(user_id=user.id)).fetchone()[0]
    min_num = cur.execute("SELECT MIN(number) FROM '{user_id}'".format(user_id=user.id)).fetchone()[0]
    revenge = cur.execute("SELECT * FROM users WHERE user_id=?", (user.id,)).fetchone()[4]
    if min_num == None:
        min_num = 0
        max_num = 0
    if revenge == None:
        revenge = 0
    i = min_num
    while revenge > 0 and i <= max_num:
        msg = cur.execute("SELECT * FROM '{user_id}' WHERE number = ?".format(user_id = user.id), (i, )).fetchone()
        if not msg[4]:
            await context.bot.set_message_reaction(chat_id=msg[2], message_id=msg[1], reaction=ReactionTypeEmoji("🤡"))
            cur.execute("UPDATE '{user_id}' SET clown = 1 WHERE number = ?".format(user_id = user.id), (i, ))
            cur.execute("UPDATE 'c{chat_id}' SET clown = 1 WHERE user_id = ? AND message_id = ?".format(chat_id = msg[2]), (user.id, msg[1]))
            db.commit()
            revenge -= 1 
        i += 1 
    cur.execute("UPDATE users SET revenge = ? WHERE user_id = ?", (revenge, user.id))
    db.commit()
            
async def do_amnesty(user, context):
    max_num = cur.execute("SELECT MAX(number) FROM '{user_id}'".format(user_id=user.id)).fetchone()[0]
    min_num = cur.execute("SELECT MIN(number) FROM '{user_id}'".format(user_id=user.id)).fetchone()[0]
    if min_num == None:
        min_num = 0
        max_num = 0
    i = min_num
    cur.execute("UPDATE users SET cursed = 0, revenge = 0 WHERE user_id = ?", (user.id,))
    db.commit()
    while i <= max_num:
        msg = cur.execute("SELECT * FROM '{user_id}' WHERE number = ?".format(user_id = user.id), (i, )).fetchone()
        if msg[4]:
            await context.bot.set_message_reaction(chat_id=msg[2], message_id=msg[1])
            cur.execute("UPDATE '{user_id}' SET clown = 0 WHERE number = ?".format(user_id = user.id), (i, ))
            cur.execute("UPDATE 'c{chat_id}' SET clown = 0 WHERE user_id = ? AND message_id = ?".format(chat_id = msg[2]), (user.id, msg[1]))
            db.commit()
        i += 1 


async def base_upd_usercommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.from_user.id == ADMIN_ID:
        print(context.args)
        print("revenge:", context.args[2])
        await db_upd_user(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name, int(context.args[0]), int(context.args[1]), int(context.args[2]), int(context.args[3]))     
        if int(context.args[2]) > 0:
            await do_revenge(update.message.reply_to_message.from_user, context)
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def base_del_usercommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.from_user.id == ADMIN_ID:
        cur.execute("DROP TABLE IF EXISTS '{user_id}'".format(user_id=update.message.reply_to_message.from_user.id))
        cur.execute("DELETE FROM users WHERE user_id=?", (update.message.reply_to_message.from_user.id,))
        db.commit()
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def base_upd_chatcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        print(context.args)
        await db_upd_chat(update.message.chat.id, update.message.chat.first_name, int(context.args[0]))     
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))


async def base_del_chatcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        cur.execute("DROP TABLE IF EXISTS 'c{chat_id}'".format(chat_id=update.message.chat.id))
        cur.execute("DELETE FROM chat WHERE chat_id=?", (update.message.chat.id,))
        db.commit()
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def dev_base_upd_usercommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        print(context.args)
        print("revenge:", context.args[2])
        await db_upd_user(context.args[0], context.args[1], int(context.args[2]), int(context.args[3]), int(context.args[4]), int(context.args[5]))     
        if int(context.args[4]) > 0:
            await do_revenge(update.message.reply_to_message.from_user, context)
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def dev_base_del_usercommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        cur.execute("DROP TABLE IF EXISTS '{user_id}'".format(user_id=context.args[0]))
        cur.execute("DELETE FROM users WHERE user_id=?", (context.args[0],))
        db.commit()
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def dev_base_upd_chatcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        print(str(context.args[0]), str(context.args[1]), int(context.args[2]))
        await db_upd_chat(str(context.args[0]), str(context.args[1]), int(context.args[2]))     
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))


async def dev_base_del_chatcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        cur.execute("DROP TABLE IF EXISTS 'c{chat_id}'".format(chat_id=context.args[0]))
        cur.execute("DELETE FROM chat WHERE chat_id=?", (context.args[0],))
        db.commit()
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))



async def protectcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.from_user.id)).fetchone()
        if update.message.from_user.id == ADMIN_ID or ( usr and usr[5] ):
            usr_ans = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.reply_to_message.from_user.id)).fetchone()
            if usr_ans:
                cur.execute("UPDATE users SET protect = 1 WHERE user_id = ?", (update.message.reply_to_message.from_user.id,))
                db.commit() 
            else:
                await db_upd_user(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name, 0, 300, 0, 1)
        else:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def unprotectcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.from_user.id)).fetchone()
        if update.message.from_user.id == ADMIN_ID or ( usr and usr[5] ):
            usr_ans = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.reply_to_message.from_user.id)).fetchone()
            if usr_ans:
                cur.execute("UPDATE users SET protect = 0 WHERE user_id = ?", (update.message.reply_to_message.from_user.id,))
                db.commit()
            else:
                await db_upd_user(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name, 0, 300, 0, 0)
        else:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))



async def amnestycommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.from_user.id)).fetchone()
        if usr and usr[5]:
            await do_amnesty(update.message.reply_to_message.from_user, context)
        else:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def revengecommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.from_user.id)).fetchone()
        if usr and usr[5]:
            cur.execute("UPDATE users SET revenge = ? WHERE user_id = ?", (int(context.args[0]), update.message.reply_to_message.from_user.id))
            db.commit()
            await do_revenge(update.message.reply_to_message.from_user, context)
        else:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def cursecommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.from_user.id)).fetchone()
        if usr and usr[5]:
            cur.execute("UPDATE users SET cursed = 1, revenge = store WHERE user_id = ?", (update.message.reply_to_message.from_user.id, ))
            db.commit()
            await do_revenge(update.message.reply_to_message.from_user, context)
        else:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))


async def clowncommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.reply_to_message.message_id, reaction=ReactionTypeEmoji("🤡"))
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.reply_to_message.from_user.id)).fetchone()
        if usr and usr[3]:
            msg = cur.execute("SELECT * FROM '{user_id}' WHERE chat_id = ? AND message_id = ?".format(user_id = update.message.reply_to_message.from_user.id), (update.effective_chat.id, update.message.reply_to_message.message_id)).fetchone()
            if msg:
                cur.execute("UPDATE '{user_id}' SET clown = 1 WHERE chat_id = ? AND message_id = ?".format(user_id = update.message.reply_to_message.from_user.id), (update.effective_chat.id, update.message.reply_to_message.message_id))
                cur.execute("UPDATE 'c{chat_id}' SET clown = 1 WHERE user_id = ? AND message_id = ?".format(chat_id = update.effective_chat.id), (update.message.reply_to_message.from_user.id, update.message.reply_to_message.message_id))
                db.commit()
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))


async def unclowncommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_message_user(update.message, 0, 300)
    if update.message.reply_to_message:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.reply_to_message.message_id)
        usr = cur.execute("SELECT * FROM users WHERE user_id == {user_id}".format(user_id=update.message.reply_to_message.from_user.id)).fetchone()
        if usr and usr[3]:
            msg = cur.execute("SELECT * FROM '{user_id}' WHERE chat_id = ? AND message_id = ?".format(user_id = update.message.reply_to_message.from_user.id), (update.effective_chat.id, update.message.reply_to_message.message_id)).fetchone()
            if msg:
                cur.execute("UPDATE '{user_id}' SET clown = 0 WHERE chat_id = ? AND message_id = ?".format(user_id = update.message.reply_to_message.from_user.id), (update.effective_chat.id, update.message.reply_to_message.message_id))
                cur.execute("UPDATE 'c{chat_id}' SET clown = 0 WHERE user_id = ? AND message_id = ?".format(chat_id = update.effective_chat.id), (update.message.reply_to_message.from_user.id, update.message.reply_to_message.message_id))
        db.commit()
    else:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=ReactionTypeEmoji("🤡"))

async def reactionh(update: Update, context: CallbackContext):
    print("clown")
    print(update.message_reaction.new_reaction)
    if update.message_reaction.new_reaction[0].emoji == "🤡":
        
        msg = get_string("c{chat_id}".format(chat_id=update.message_reaction.chat.id), "message_id", update.message_reaction.message_id)
        if msg:
            user_react = get_string("users", "user_id", update.message_reaction.user.id)
            user_msg = get_string("users", "user_id", msg[2])
            if user_msg[5] and user_react and (not user_react[5]):
                cur.execute("UPDATE users SET revenge = 1 WHERE user_id = ?", (update.message_reaction.user.id, ))
                db.commit()
                await do_revenge(update.message_reaction.user, context)
            if user_msg[5] and (not user_react):
                max_number = cur.execute("SELECT MAX(number) FROM 'c{chat_id}' WHERE user_id = ? AND clown = 0".format(chat_id=update.message_reaction.chat.id), (update.message_reaction.user.id,)).fetchone()[0]
                print (max_number)
                if max_number != None:
                    cln_msg = cur.execute("SELECT * FROM 'c{chat_id}' WHERE number = ?".format(chat_id=update.message_reaction.chat.id), (max_number,)).fetchone()
                    if cln_msg != None:
                        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=cln_msg[1], reaction=ReactionTypeEmoji("🤡"))
                        cur.execute("UPDATE 'c{chat_id}' SET clown = 1 WHERE number = ?".format(update.effective_chat.id), (cln_msg[0],))
            if user_react[5]:
                cur.execute("UPDATE '{user_id}' SET clown_from_prot = 1 WHERE chat_id = ? AND message_id = ?".format(user_id=user_msg[0]), (update.message_reaction.chat.id, msg[1]))
                cur.execute("UPDATE 'c{chat_id}' SET clown_from_prot = 1 WHERE message_id = ?".format(chat_id=update.message_reaction.chat.id), (msg[1], ))

                

            


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    db_start()
    

    reaction_handler = MessageReactionHandler(reactionh)

    base_upd_user_handler = CommandHandler('base_upd_user', base_upd_usercommand, has_args=4)
    base_del_user_handler = CommandHandler('base_del_user', base_del_usercommand)
    base_upd_chat_handler = CommandHandler('base_upd_chat', base_upd_chatcommand, has_args=1)
    base_del_chat_handler = CommandHandler('base_del_chat', base_del_chatcommand)
    dev_base_upd_user_handler = CommandHandler('dev_base_upd_user', dev_base_upd_usercommand, has_args=6)
    dev_base_del_user_handler = CommandHandler('dev_base_del_user', dev_base_del_usercommand, has_args=1)
    dev_base_upd_chat_handler = CommandHandler('dev_base_upd_chat', dev_base_upd_chatcommand, has_args=3)
    dev_base_del_chat_handler = CommandHandler('dev_base_del_chat', dev_base_del_chatcommand, has_args=1)
    
    start_handler = CommandHandler('start', start)
    clown_handler = CommandHandler('clown', clowncommand)
    unclown_handler = CommandHandler('unclown', unclowncommand)
    amnesty_handler = CommandHandler('amnesty', amnestycommand)
    revenge_handler = CommandHandler('revenge', revengecommand, has_args = 1)
    curse_handler = CommandHandler('curse', cursecommand)
    protect_handler = CommandHandler('protect', protectcommand)
    unprotect_handler = CommandHandler('unprotect', unprotectcommand)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), messageh)


    application.add_handler(start_handler)
    application.add_handler(clown_handler)
    application.add_handler(message_handler)
    application.add_handler(unclown_handler)
    application.add_handler(base_upd_user_handler)
    application.add_handler(base_del_user_handler)
    application.add_handler(base_upd_chat_handler)
    application.add_handler(base_del_chat_handler)
    application.add_handler(dev_base_upd_user_handler)
    application.add_handler(dev_base_del_user_handler)
    application.add_handler(dev_base_upd_chat_handler)
    application.add_handler(dev_base_del_chat_handler)
    application.add_handler(amnesty_handler)
    application.add_handler(revenge_handler)
    application.add_handler(curse_handler)
    application.add_handler(protect_handler)
    application.add_handler(unprotect_handler)
    application.add_handler(reaction_handler)

    application.run_polling( allowed_updates = ["message", "edited_message", "channel_post", "edited_channel_post", "inline_query", "chosen_inline_result", "callback_query", "shipping_query", "pre_checkout_query", "poll", "poll_answer", "my_chat_member", "chat_member", "chat_join_request", "chat_boost", "removed_chat_boost", "message_reaction", "message_reaction_count"])
   

import sys

import logging

import urllib3
import json
import requests

from telegram import InlineQueryResultArticle, InputTextMessageContent

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler

if len(sys.argv) != 2:
    raise ValueError('Please provide token as parameter')

token = sys.argv[1]

urllib3.disable_warnings()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

updater = Updater(token = token, use_context=True)

dispatcher = updater.dispatcher

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def stop(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bye bye!")
    updater.stop()

stop_handler = CommandHandler('stop', stop)
dispatcher.add_handler(stop_handler)

def check_alternative(text):
    print(text)
    httpResponse = requests.get(f"https://hebrew-academy.org.il/wp-admin/admin-ajax.php?action=load_halufot_text&input={text}&_ajax_nonce=55ec8a0336", verify = False)

    if httpResponse.text == "":
        chatResponse = f"חוששני שאיני יודע את החלופה העברית ל{text}"
    else:
        jsonResponse = json.loads(httpResponse.text)
        if len(jsonResponse) == 0:
            chatResponse = "חלה שגיאה!"
        else:
            response = jsonResponse[0]
            chatResponse = f"""בלע\"ז: {response.get("loazitMenukad")}
    בשפת נכר: {response.get("english")}
    בלשון הקודש: {response.get("ivritMenukad")}"""
    
    return chatResponse

def check_alternative_handle(update, context):
    if len(context.args) > 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=check_alternative(text=context.args[0]))

check_alternative_handler = CommandHandler('alt', check_alternative_handle)
dispatcher.add_handler(check_alternative_handler)

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

#echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
#dispatcher.add_handler(echo_handler)

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

#unknown_handler = MessageHandler(Filters.command, unknown)
#dispatcher.add_handler(unknown_handler)

def inline(update, context):
    query = update.inline_query.query
    if not query:
        return
    results = list()

    answer = check_alternative(query)

    results.append(
        InlineQueryResultArticle(
            id="חלופה",
            title=f'החלופה העברית ל{query} היא: {answer}',
            input_message_content=InputTextMessageContent(answer)
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)

inline_handler = InlineQueryHandler(inline)
dispatcher.add_handler(inline_handler)

updater.start_polling()
updater.idle()
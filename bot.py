import sys

import os, signal, threading

import logging

import urllib3
import json
import requests

from telegram import InlineQueryResultArticle, InputTextMessageContent

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler

if len(sys.argv) < 2:
    raise ValueError('Please provide token as parameter')

token = sys.argv[1]

if (len(sys.argv) < 3):
    chatIdControling = None
else:
    chatIdControling = int(sys.argv[2])

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
    print("chat id: ", update.effective_chat.id)

    if chatIdControling and chatIdControling != update.effective_chat.id:
        print("unauthorized invocation of stop command")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Bye bye!")
        context.bot.deleteWebhook()
        #context.bot.close()

        def send_stop():
            updater.stop()

        sender = threading.Thread(target=send_stop, name='sender')
        sender.start()
        #sender.join()
        os.kill(os.getpid(), signal.SIGINT)

stop_handler = CommandHandler('stop', stop)
dispatcher.add_handler(stop_handler)

#halufon_nonce = "2b4b4494f8"

def renew_halufon_nonce():
	httpResponseText = requests.get("https://hebrew-academy.org.il/איך-אומרים-בעברית/", verify = False).text
	
	definition_str = 'var halufon_nonce = \"'
	
	halufon_nonce_def_start_loc = httpResponseText.find(definition_str) + len(definition_str)
	halufon_nonce_def_end_loc = httpResponseText.find('\"', halufon_nonce_def_start_loc);
	
	global halufon_nonce
	halufon_nonce = httpResponseText[halufon_nonce_def_start_loc : halufon_nonce_def_end_loc]
	
	print(halufon_nonce_def_start_loc, halufon_nonce_def_end_loc, halufon_nonce)

renew_halufon_nonce()

def check_alternative(text, redo = True):
    print(text)
    
    url = f"https://hebrew-academy.org.il/wp-admin/admin-ajax.php?action=load_halufot_text&input={text}&_ajax_nonce={halufon_nonce}"
    print("quering url:", url)
    httpResponse = requests.get(url, verify = False)

    if httpResponse.text == "":
        chatResponse = f"חוששני שאיני יודע את החלופה העברית ל{text}"
    else:
        jsonResponse = json.loads(httpResponse.text)
        
        if isinstance(jsonResponse, int) and redo:
            renew_halufon_nonce()
            return check_alternative(text, False)
        # otherwise
		
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

print("end")
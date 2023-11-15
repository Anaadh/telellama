import configparser

import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

config = configparser.ConfigParser()
config.read("config.ini")

API_ID = config.get("pyrogram","API_ID")
API_HASH = config.get("pyrogram","API_HASH")
BOT_TOKEN = config.get("pyrogram","BOT_TOKEN")
API_URL = config.get("pyrogram","API_URL")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

chat_history = {}

@app.on_message(filters.command("start"))
def start(client, message):
  text = "Hi there! I'm an AI assistant bot ready to chat with you."
  app.send_message(message.chat.id, text)

@app.on_message(filters.command("help"))
def help(client, message):
  text = "I can have natural conversations. Use the inline 'Continue' buttons to keep chatting with me. Type /reset to erase our chat history and start fresh."
  app.send_message(message.chat.id, text)

@app.on_message(filters.command("reset"))
def reset(client, message):
  chat_id = message.chat.id
  chat_history[chat_id] = []
  app.send_message(message.chat.id, "Our chat history has been completely erased!")

@app.on_message(filters.text)
def chat(client, message):

  chat_id = message.chat.id
  history = chat_history.get(chat_id, [])

  response = requests.post(API_URL, json={"user_input": message.text, "history": {"internal": history, "visible": history}})

  if response.ok:
    ai_text = response.json()["results"][0]["history"]["visible"][-1][1]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="Continue", callback_data="continue")]])
    app.send_message(chat_id, ai_text, reply_markup=keyboard)

    history.append([message.text, ai_text])
    chat_history[chat_id] = history

  else:
    app.send_message(chat_id, "Sorry, I'm having some trouble connecting right now. Please try again later.")

@app.on_callback_query(filters.regex("continue"))
def continue_callback(client, callback_query):
    chat_id = callback_query.message.chat.id

    last_msg = chat_history[chat_id][-1][0]
    response = requests.post(API_URL, json={"user_input": last_msg, "history": {"internal": chat_history[chat_id], "visible": chat_history[chat_id]}, "_continue": True})

    if response.ok:
        ai_text = response.json()["results"][0]["history"]["visible"][-1][1]

        # Edit the existing message to show the extended version
        chat_history[chat_id][-1][1] = ai_text
        new_text = chat_history[chat_id][-1][1]

        # Create an inline keyboard with a "Continue" button
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="Continue", callback_data="continue")]])

        # Edit the message to update the content and keep the "Continue" button
        callback_query.edit_message_text(new_text, reply_markup=keyboard)

    else:
        app.send_message(chat_id, "Sorry, I'm having trouble connecting right now. Please try again later.")



app.run()
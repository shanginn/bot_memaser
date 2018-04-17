#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#

from telegram.ext import Updater, MessageHandler
from vk_manager import VKM
import traceback
import urlmarker
import logging
import sqlite3
import yaml
import sys
import re
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    filemode='w',
)

logger = logging.getLogger(__name__)

# Читаем конфиги
try:
    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile)
        print("Config loaded")
except BaseException:
    print("config.yml file is not exists! Please create it first.")
    sys.exit()

if config['telegram-token'] == '':
    print("Please configure your Telegram bot token")
    sys.exit()

if config['vk-login'] == '' or config['vk-password'] == '':
    print("Please add your Vkontakte credentials")
    sys.exit()

if config['vk-group-id'] == '':
    print("Please add Vkontakte group id")
    sys.exit()

proxy = None
if config['socks5-proxy']['address'] and config['socks5-proxy']['port']:
    proxy = config['socks5-proxy']

manager = VKM(config['vk-login'], config['vk-password'], config['vk-group-id'], proxy)
url_regexp = re.compile(urlmarker.WEB_URL_REGEX)
db = sqlite3.connect('history.db').cursor()

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))
    # bot.sendMessage(
    #     update.message.chat_id,
    #     text='Update "%s" caused error "%s"' % (update, error)
    # )


def handle_message(bot, update):
    try:
        url, caption = parse_message(bot, update.message)
        if url:
            response = manager.handle_url(url, caption)

            if 'post_id' in response:
                #TODO: record actions in database
                print(response, update)
            return response
    except Exception:
        traceback.print_exc()


def parse_message(bot, message):
    if message.photo:
        # Получаем фотку наилучшего качества(последнюю в массиве)
        photo = message.photo[-1]

        # Описание к фотке
        caption = message['caption']

        # url фото на сервере Telegram
        image_url = bot.getFile(photo['file_id'])['file_path']

        return image_url, caption
    elif message.text:
        # Если в сообщении были ссылки
        matches = url_regexp.split(message.text)[1:]

        if matches:
            urls_with_captions = list(zip(*[matches[i::2] for i in range(2)]))
            # TODO: handle multiple links in one message
            return urls_with_captions[0]

    return False, False


def main():
    print("Starting updater...")
    updater = Updater(
        config['telegram-token'],
        request_kwargs={
            'proxy_url': 'socks5://%s:%d/' % (proxy['address'], proxy['port']),
            'urllib3_proxy_kwargs': {'username': proxy['username'], 'password': proxy['password']}
        } if proxy else None,
    )

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    #dp.add_handler(CommandHandler("help", start))
    print("Adding handlers...")
    dp.add_handler(MessageHandler(False, handle_message))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    print("idle.")
    updater.idle()


if __name__ == '__main__':
    main()

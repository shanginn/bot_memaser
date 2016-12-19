#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from telegram.ext import Updater, MessageHandler
import logging, yaml, sys, os, urllib, urlparse
from vk_manager import VKM

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
except BaseException:
    print "config.yml file is not exists! Please create it first."
    sys.exit()

if config['telegram-token'] == '':
    print "Please configure your Telegram bot token"
    sys.exit()

if config['vk-login'] == '' or config['vk-password'] == '':
    print "Please add your Vkontakte credentials"
    sys.exit()

if config['vk-group-id'] == '':
    print "Please add Vkontakte group id"
    sys.exit()


manager = VKM(config['vk-login'], config['vk-password'], config['vk-group-id'])


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
    # bot.sendMessage(
    #     update.message.chat_id,
    #     text='Update "%s" caused error "%s"' % (update, error)
    # )


def upload_image(bot, update):
    try:
        if update.message.photo:
            # Получаем фотку наилучшего качества(последнюю в массиве)
            photo = update.message.photo[-1]

            # Описание к фотке
            caption = update.message['caption']


            # url фото на сервере Telegram
            image_url = bot.getFile(photo['file_id'])['file_path']

            # Имя файла с корректным расширением из url
            filename = urlparse.urlsplit(image_url.strip()).path.split('/')[-1]

            # Загружаем фотку на диск
            urllib.urlretrieve(image_url, filename)

            # Загружаем фотку на стену группы Вконтакте
            manager.upload_image(filename, caption)

            # Удаляем фотку
            os.remove(filename)
    except Exception:
        pass


def main():
    updater = Updater(config['telegram-token'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    #dp.add_handler(CommandHandler("help", start))
    dp.add_handler(MessageHandler(False, upload_image))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

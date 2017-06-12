#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from telegram.ext import Updater, MessageHandler
import logging, yaml, sys, os, urlparse
from vk_manager import VKM
import urlmarker, re
import traceback

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
        print "Config loaded"
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


def handle_message(bot, update):
    try:
        if update.message.photo:
            # Получаем фотку наилучшего качества(последнюю в массиве)
            photo = update.message.photo[-1]

            # Описание к фотке
            caption = update.message['caption']

            # url фото на сервере Telegram
            image_url = bot.getFile(photo['file_id'])['file_path']

            return manager.post_image_from_url(image_url, caption)
        elif update.message.text:
            # Если в сообщении были ссылки
            for url in extract_urls(update.message.text):
                handle_url(url)

    except Exception:
        traceback.print_exc()


def handle_url(url, caption=''):
    # Если это ссылка на видео
    if any(video_platform in url for video_platform in config['supported-video-platforms']):
        video = manager.post_video_from_url(url, caption)

        manager.upload.vk.method('video.addToAlbum', {
            'target_id': '-%d' % config['vk-group-id'],
            'album_id': '-2',
            'owner_id': '-%d' % config['vk-group-id'],
            'video_id': video['video_id']
        })

        return video

    # Расширение файла из url
    extension = urlparse.urlsplit(url.strip()).path.split('/')[-1].split('.')[-1]

    # Проверка на изображение
    if extension in ['jpg', 'png']:
        return manager.post_image_from_url(url, caption)
    elif extension == 'gif':
        return manager.post_gif_from_url(url, caption)

    return manager.post_to_wall(caption, url)


def main():
    print "Starting updater..."
    updater = Updater(config['telegram-token'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    #dp.add_handler(CommandHandler("help", start))
    print "Adding handlers..."
    dp.add_handler(MessageHandler(False, handle_message))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    print "idle."
    updater.idle()


def extract_urls(text):
    return re.findall(urlmarker.WEB_URL_REGEX,text)


if __name__ == '__main__':
    main()

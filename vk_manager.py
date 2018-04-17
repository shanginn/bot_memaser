#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import vk_api, sys, os, urllib
import socks
import socket
import imghdr
import tempfile

"""
Менеджер Вконтакте.
Используется vk_api (https://github.com/python273/vk_api)
Загружает фотки на стену группы ВК.

Я не нашел способ загрузки фоточек через токен,
поэтому используется логин и пароль админа группы.
"""

class VKM:
    def auth_handler(self):
        # Если у вас включена 2-х факторная авторизация,
        # то при запуске нужно вводить код
        while True:
            try:
                two_FA_code = int(input("Please enter 2FA code: "))
            except ValueError:
                print("Wrong input")
                continue
            else:
                break

        return two_FA_code, True

    def __init__(self, login, password, group_id, proxy):
        self.allowed_image_extensions = ['jpeg', 'jpg', 'gif', 'png', 'gif']
        self.supported_video_platforms = ["youtube.com", "vimeo.com", "youtu.be", "coub.com", "rutube.ru"]

        for i in range(1, 4):
            try:
                vk_session = vk_api.VkApi(login, password, auth_handler=self.auth_handler, app_id=5958197)

                vk_session.auth()
            except vk_api.AuthError as error_msg:
                print(error_msg)

                if i >= 3:
                    sys.exit()
            else:
                continue

        self.vk_session = vk_session
        self.group_id = group_id
        self.api = self.vk_session.get_api()
        self.upload = vk_api.VkUpload(self.vk_session)

        if proxy:
            socks.set_default_proxy(
                socks.SOCKS5,
                addr=proxy['address'],
                port=proxy['port'],
                username=proxy['username'],
                password=proxy['password']
            )
            socket.socket = socks.socksocket

    def upload_images_to_wall(self, paths):
        return self.upload.photo_wall(
            paths,
            group_id=self.group_id
        )

    def upload_video_to_wall(self, video):
        return self.upload.video(
            video_file=video,
            wallpost=True,
            group_id=self.group_id
        )

    def upload_document_to_wall(self, path):
        return self.upload.document_wall(
            path,
            #group_id=self.group_id
        )[0]

    def post_images(self, image_paths, caption=''):
        # Сначала нужно загрузть фотку на сервера ВК
        photos = self.upload_images_to_wall(image_paths)

        # Потом получить её ID
        attachments = ','.join(['photo{}_{}'.format(
            photo['owner_id'], photo['id']
        ) for photo in photos])

        # И запостить на стену группы
        return self.post_to_wall(caption, attachments)

    def post_image_from_url(self, url, caption=''):
        # Загружаем фотку на диск
        filepath, extension = self.get_url(url)

        # Проверка расширения после скачивания
        if extension not in self.allowed_image_extensions:
            print("Error: %s is not an image (allowed extensions: %s)" % (filepath, ','.join(self.allowed_image_extensions)))
            status = False
        else:
            # Загружаем фотку на стену группы Вконтакте
            status = self.post_images(filepath, caption)

        # Удаляем фотку
        os.remove(filepath)

        return status

    def post_gif_from_url(self, url, caption=''):
        filepath, extension = self.get_url(url)

        if extension != 'gif':
            print("Error: %s is not a gif" % filepath)

            status = False
        else:
            status = self.post_document(filepath, caption)

        os.remove(filepath)

        return status

    def post_document(self, filepath, caption):
        # Сначала нужно загрузть фотку на сервера ВК
        document = self.upload_document_to_wall(filepath)

        # Потом получить её ID
        attachments = 'doc{}_{}'.format(
            document['owner_id'], document['id']
        )

        # И запостить на стену группы
        return self.post_to_wall(caption, attachments)

    def post_to_wall(self, message, attachments=None):
        return self.api.wall.post(
            owner_id='-%d' % self.group_id,
            attachments=attachments,
            message=message
        )

    def get_url(self, url):
        filepath, headers = urllib.request.urlretrieve(url, tempfile.gettempdir() + '/' + url.split('/')[-1])
        extension = imghdr.what(filepath)

        return filepath, extension

    def handle_url(self, url, caption=''):
        if any(video_platform in url for video_platform in self.supported_video_platforms):
            # Если это ссылка на видео
            return self.upload.video(link=url, group_id=self.group_id, wallpost=True)
        else:
            # Расширение файла из url
            extension = urllib.parse.urlsplit(url.strip()).path.split('/')[-1].split('.')[-1]

            # Проверка на изображение
            if extension in ['jpg', 'jpeg', 'png']:
                return self.post_image_from_url(url, caption)
            elif extension == 'gif':
                return self.post_gif_from_url(url, caption)

            return self.post_to_wall(caption, url)

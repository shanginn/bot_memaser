#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import vk_api, sys, os, urllib

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
                two_FA_code = int(raw_input("Please enter 2FA code: "))
            except ValueError:
                print("Wrong input")
                continue
            else:
                break

        return two_FA_code, True

    def __init__(self, login, password, group_id):
        self.allowed_image_extensions = ['.jpg', '.gif', '.png']

        for i in range(1,4):
            try:
                vk_session = vk_api.VkApi(login, password, auth_handler=self.auth_handler, app_id=None)

                vk_session.auth()
            except vk_api.AuthError as error_msg:
                print error_msg

                if i >= 3:
                    sys.exit()
            else:
                continue

        self.vk_session = vk_session
        self.group_id = group_id
        self.api = self.vk_session.get_api()
        self.upload = vk_api.VkUpload(self.vk_session)

    def upload_images_to_wall(self, paths):
        return self.upload.photo_wall(
            paths,
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

    def post_image_from_url(self, url, caption = ''):
        # Загружаем фотку на диск
        filepath, filename, extension, headers = self.get_url(url)

        # Проверка расширения после скачивания
        if extension not in self.allowed_image_extensions:
            print "Error: %s is not image (allowed extensions: %s)" % (filepath, ','.join(self.allowed_image_extensions))
            return False

        # Загружаем фотку на стену группы Вконтакте
        status = self.post_images(filepath, caption)

        # Удаляем фотку
        os.remove(filepath)

        return status

    def post_gif_from_url(self, url, caption):
        filepath, filename, extension, headers = self.get_url(url)

        if extension != '.gif':
            print "Error: %s is not a gif" % filepath

            return False

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


    def post_to_wall(self, message, attachments = None):
        return self.api.wall.post(
            owner_id='-%d' % self.group_id,
            attachments=attachments,
            message=message
        )

    def get_url(self, url):
        filepath, headers = urllib.urlretrieve(url)
        filename, extension = os.path.splitext(filepath)

        return filepath, filename, extension, headers

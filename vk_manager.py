#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import vk_api, sys

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
        for i in range(1,4):
            try:
                vk_session = vk_api.VkApi(login, password, auth_handler=self.auth_handler)

                vk_session.auth()
            except vk_api.AuthError as error_msg:
                print error_msg

                if i > 3:
                    sys.exit()
            else:
                continue

        self.vk_session = vk_session
        self.group_id = group_id
        self.api = self.vk_session.get_api()

    def upload_image(self, image_path, caption=''):
        # Сначала нужно загрузть фотку на сервера ВК
        upload = vk_api.VkUpload(self.vk_session)

        photo = upload.photo_wall(
            image_path,
            group_id=self.group_id
        )

        # Потом получить её ID
        vk_photo_id = 'photo{}_{}'.format(
            photo[0]['owner_id'], photo[0]['id']
        )

        # И запостить на стену группы
        self.api.wall.post(
            owner_id='-%d' % self.group_id,
            attachments=vk_photo_id,
            message=caption
        )

# -*- coding: utf-8 -*-

# MIT License
# https://github.com/invernizzi/hiplogging

import logging
import hipchat


class HipChat(object):

    def __init__(self, admin_token, default_room=None, url='https://hipchat.com/v2'):
        self.api = hipchat.Hip(admin_token, url)
        self.default_room = default_room
        self.room_ids_cache = {}

    def find_room_id(self, name):
        room_id = self.room_ids_cache.get(name)
        if not room_id:
            try:
                room_id = self.api.find_room(name)['room_id']
            except TypeError:
                print('WARNING: hipchat room "{0}" not found!'.format(name))
                return None
            self.room_ids_cache[name] = room_id
        return room_id

    def send_message(self, message, sender='log', color='yellow', room=None):
        if not room:
            room = self.default_room
        room_id = room
        if room_id is None:
            return
        self.api.post_notification_to_room(
            room,
            message,
            color)


class HipChatHandler(logging.Handler):

    def __init__(self, admin_token, room, url='https://hipchat.com/v2'):
        logging.Handler.__init__(self)
        self.api = HipChat(admin_token, room, url)

    def emit(self, record):
        if hasattr(record, "color"):
            color = record.color
        else:
            color=self.__color_for_level(record.levelno)
        self.api.send_message(
            self.format(record),
            color=color
        )

    def __color_for_level(self, levelno):
        if levelno > logging.WARNING:
            return 'red'
        if levelno == logging.WARNING:
            return 'yellow'
        if levelno == logging.INFO:
            return 'green'
        if levelno == logging.DEBUG:
            return 'gray'
        return 'purple'

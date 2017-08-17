#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import time

from danmu import DanMuClient
from xml.sax.saxutils import escape
from datetime import datetime
from utils.common import log_print

class DanMuFileMaker():
    def __init__(self, url, dm_dir):
        self.live_id = url[url.rfind('/')+1:]
        self.danmu_file = os.path.join(dm_dir, '%s%s' % (self.live_id, '.xml'))
        self.danmu_header = '<?xml version="1.0" encoding="UTF-8"?><i>\n'
        self.danmu_footer = '</i>\n'
        self.danmu_time_start = 0
        self.danmu_type = 1
        self.danmu_font_size = 25
        self.danmu_unix_time = 0
        self.danmu_color = [16777215, 16711680, 2000880, 8046667, 16744192, 10172916, 16738740]
        self.noble_color = [4814813, 7894262, 14103839, 16163118]

        self.__danmu_buffer = []
        self.__danmu_buffer_size = 65536
        #if dmc.isValid == False? return ? try?
        self.dmc = DanMuClient(url)

        @self.dmc.danmu
        def danmu_fn(msg):
            cur_time = time.time()
            dm_time = cur_time - self.danmu_time_start
            # add noble name before danmu content
            nickname = msg['NickName']
            content = escape(msg['Content'])
            nl = 0
            if 'nl' in msg:
                nl = int(msg['nl'])
            if nl and nl > 2 and nl < 7:
                content = '【{name}】{content}'.format(
                    name = nickname,
                    content = content
                )
                color = self.noble_color[nl-3]
                danmu_size = 30
            else:
                color = self.danmu_color[int(msg['Color'])]
                danmu_size = self.danmu_font_size
            # 粉丝牌等级
            card_level = msg['bl']
            # 粉丝牌昵称
            card_nickname = msg['bnn']
            # 用户等级
            user_level = msg['level']
            # uid
            uid = msg['uid']
            danmu_data = str.format('<d p=\"%f,%d,%d,%d,%d,%s,%s,%s,%s,%s\">%s</d>\n'
                                   % (dm_time, self.danmu_type,
                                      danmu_size, color, int(time.time()),
                                      user_level, card_level, nickname,
                                      card_nickname, uid, content))
            self.__danmu_buffer.append(danmu_data)

            if len(self.__danmu_buffer) >= self.__danmu_buffer_size:
                with open(self.danmu_file, 'a+',
                          encoding='utf-8') as danmu_file:
                    danmu_file.writelines(self.__danmu_buffer)
                self.__danmu_buffer = []

    def start(self):
        self.dmc.default(None)
        self.dmc.gift(None)

        with open(self.danmu_file, 'w',
                  encoding='utf-8') as danmu_file:
            danmu_file.write(self.danmu_header)

        self.danmu_time_start = time.time()
        # self.dmc.start(blockThread = True)
        self.dmc.start(blockThread = False)

    def stop(self):
        log_print('DanMuFileMaker stop')
        self.dmc.stop()
        if self.__danmu_buffer:
            with open(self.danmu_file, 'a+',
                      encoding='utf-8') as danmu_file:
                danmu_file.writelines(self.__danmu_buffer)
            self.__danmu_buffer = []

        with open(self.danmu_file, 'a+',
                  encoding='utf-8') as danmu_file:
            danmu_file.write(self.danmu_footer)

#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
douyu opencdn api
'''

import json
import re
import urllib.request

URL_LIVE_DOUYU = 'https://www.douyu.com/'
URL_API_ROOM = 'http://open.douyucdn.cn/api/RoomApi/room/'

STATUS_ROOM_ONLINE = '1'
STATUS_ROOM_OFFLINE = '2'


def _get_room_info(room_id_number):
    headers = {'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'
                              ' AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/50.0.2661.102 Safari/537.36')
               }
    try:
        request = urllib.request.Request(URL_API_ROOM + room_id_number,
                                         headers=headers)
        resp = urllib.request.urlopen(request, timeout = 30).read()
        resp_json = json.loads(resp)
    except:
        print('_get_room_info except')
        resp_json = ''
    return resp_json


def is_room_online(room_id_number):
    room_info = _get_room_info(room_id_number)
    try:
        if room_info['data']['room_status'] == STATUS_ROOM_ONLINE:
            return True
        else:
            return False
    except:
        print('is_room_online except')
        print(room_info)
        return False


def get_room_title(room_id_number):
    room_info = _get_room_info(room_id_number)
    # do some format string?
    return room_info['data']['room_name']


def get_room_id_number(room_id_number):
    room_info = _get_room_info(room_id_number)
    return room_info['data']['room_id']


def save_json(room_id_number, to_file):
    room_info = _get_room_info(room_id_number)
    if not room_info:
        return False
    with open(to_file, 'w', encoding='utf-8', errors='ignore') as json_file:
        json.dump(room_info, json_file)
    return True

def test():
    # print('zard online status: ' + str(is_room_online('zard')))
    print(get_room_title('zard'))
    print(is_room_online('zard'))
    save_json('zard', 'test.json')


if __name__ == '__main__':
    test()

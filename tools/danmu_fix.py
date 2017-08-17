#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os

def get_danmu_sec(danmu):
    res = re.findall(r'p="(\d+)\.', danmu)
    if not res:
        return -1
    return int(res[0])

def set_danmu_sec(danmu, sec):
    res = re.findall(r'p="(\d+)\.', danmu)
    if not res:
        return danmu
    if sec < 0:
        return danmu
    danmu_fixed = re.sub(r'p="(\d+)\.', 'p="{sec}.'.format(sec = sec), danmu,
                         count = 1)
    return danmu_fixed

def fix_danmu(danmu_file):
    if not os.path.exists(danmu_file):
        return
    danmu_list = []
    with open(danmu_file, 'r', encoding='utf-8', errors='ignore') as dm_file:
        for line in dm_file:
            if re.findall(r',\d{1,2},([^,]+),[^,]*">', line):
                danmu_list.append(line)

if __name__ == '__main__':
    pass

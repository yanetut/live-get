#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from datetime import timedelta

def splite_danmu(dm_file, sp_time):
    if not os.path.exists(dm_file):
        return
    dm_name = os.path.basename(dm_file)
    danmu_time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', dm_name)[0]
    danmu_time_start = datetime.strptime(danmu_time_start_str, '%H-%M')
    danmu_time_end_str = re.findall(r'_([-+]?\d+-[-+]?\d+)\.', dm_name)[0]
    sp_time_sec = sp_time
    danmu_time_end_sp1 = danmu_time_start + timedelta(seconds = sp_time_sec)
    danmu_time_end_sp1_str = danmu_time_end_sp1.strftime('%H-%M')
    danmu_sp1_buff = []
    danmu_sp2_buff = []
    danmu_header = '<?xml version="1.0" encoding="UTF-8"?><i>\n'
    danmu_footer = '</i>\n'
    danmu_sp1_buff.append(danmu_header)
    danmu_sp2_buff.append(danmu_header)
    with open(dm_file, 'r', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_file:
            time = re.findall(r'p="(\d+).', line)
            if time:
                sec = int(time[0])
                if sec < sp_time_sec:
                    danmu_sp1_buff.append(line)
                else:
                    sec_sp2 = sec - sp_time_sec
                    line_sp2 = re.sub(r'p="(\d+).', r'p="{time}.'
                                      .format(time = sec_sp2), line)
                    danmu_sp2_buff.append(line_sp2)
    danmu_sp1_buff.append(danmu_footer)
    danmu_sp2_buff.append(danmu_footer)
    danmu_sp1_name = 'zard__{t1}_{t2}.xml'.format(
        t1 = danmu_time_start_str,
        t2 = danmu_time_end_sp1_str
    )
    danmu_sp2_name = 'zard__{t1}_{t2}.xml'.format(
        t1 = danmu_time_end_sp1_str,
        t2 = danmu_time_end_str
    )
    with open(danmu_sp1_name, 'w', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_sp1_buff:
            danmu_file.write(line)
    with open(danmu_sp2_name, 'w', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_sp2_buff:
            danmu_file.write(line)

def delay_danmu(dm_file, delay_sec):
    if not os.path.exists(dm_file):
        return
    dm_name = os.path.basename(dm_file)
    danmu_sp1_buff = []
    with open(dm_file, 'r', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_file:
            time = re.findall(r'p="(\d+).', line)
            if time:
                sec = int(time[0])
                sec_delay = sec - delay_sec
                if sec_delay > 0:
                    line_delay = re.sub(r'p="(\d+).', r'p="{time}.'
                                        .format(time = sec_delay), line)
                    danmu_sp1_buff.append(line_delay)
            else:
                danmu_sp1_buff.append(line)
    danmu_sp1_name = '{delay}_{name}'.format(
        delay = delay_sec,
        name = dm_name
    )
    with open(danmu_sp1_name, 'w', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_sp1_buff:
            danmu_file.write(line)

if __name__ == '__main__':
    dm_file = os.path.join(os.getcwd(), 'zard__14-32_16-14.xml')
    splite_danmu(dm_file, 3196)
    # dm_file = os.path.join(os.getcwd(), 'zard__02-21_04-08.xml')
    # delay_danmu(dm_file, 5551)

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from datetime import datetime, timedelta

sys.path.append('..')
from utils.common import makesure_dir
from utils.common import log_print
from utils.common import get_delta_minute

# return moment: {
# <int> max_count,
# <int> max_sec_start,
# <int> sec_duration,
# <str> danmu_file,
# <str> max_time_start,
# }
def get_moment(moment_name, moment_dir):
    max_count = 0
    with open(os.path.join(moment_dir, moment_name), 'r',
        encoding='utf-8', errors='ignore') as dm_file:
        for line in dm_file:
            max_count += 1
    max_sec_start = 0
    sec_duration = 180
    # danmu_file, used in _get_moment_name
    day = int(re.findall(r'__day(\d)_', moment_name)[0])
    moment_date_str = os.path.basename(moment_dir)
    moment_date = datetime.strptime(moment_date_str, '%Y-%m-%d')
    if day == 2:
        moment_date = moment_date + timedelta(days=1)
        moment_date_str = moment_date.strftime('%Y-%m-%d')
    danmu_file = os.path.join('.', moment_date_str, moment_name)
    danmu_time_start_str = re.findall(r'_([-+]?\d+-[-+]?\d+).xml$',
        moment_name)[0]
    max_time_start = datetime.strptime(danmu_time_start_str, '%H-%M')
    moment = ({'max_count': max_count,
               'max_sec_start': max_sec_start,
               'sec_duration': sec_duration,
               'danmu_file': danmu_file,
               'max_time_start': max_time_start})
    return moment

# return moments: {
# <int> max_count,
# <int> max_sec_start,
# <int> sec_duration,
# <str> danmu_file,
# <str> max_time_start,
# }
def get_topN_moments(danmu, sec_duration, top_n):
    # danmu duration < sec_duration
    total_duration = get_delta_minute(os.path.basename(danmu)) * 60
    min_duration = sec_duration * top_n + 60
    if total_duration < min_duration:
        log_print('too small no need moment ' + 
                  'total_duration: %d, min_duration: %d' %
                  (total_duration, min_duration))
        return []
    top_moments = []
    danmu_count = {}
    with open(danmu, 'r', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_file:
            time = re.findall(r'p="(\d+).', line)
            if time:
                time_sec = time[0]
                if time_sec in danmu_count:
                    danmu_count[time_sec] += 1
                else:
                    danmu_count[time_sec] = 1
    for i in range(top_n):
        max_count = 0
        max_sec_start = list(danmu_count)[0]
        for danmu_sec in danmu_count:
            tmp_count = 0
            r1 = int(danmu_sec)
            r2 = int(r1 + sec_duration / 3 * 2 + 1)
            if r1 - sec_duration / 6 < 0:
                r1_before = 0
            else:
                r1_before = int(r1 - sec_duration / 6)
            r2_after = int(r2 + sec_duration / 6)
            set1 = set(range(r1_before, r2_after))
            if top_moments:
                intersection = False
                for moment in top_moments:
                    moment_r1 = int(moment['max_sec_start'])
                    moment_r2 = (moment_r1 + sec_duration + 1 if moment_r1 + sec_duration + 1 >
                                 int(list(danmu_count)[-1]) else int(list(danmu_count)[-1]) )
                    moment_set = set(range(moment_r1, moment_r2))
                    if moment_set.intersection(set1):
                        intersection = True
                        break
                if intersection:
                    continue
            for sec in range(r1, r2):
                key = str(sec)
                if key in danmu_count:
                    tmp_count += danmu_count[key]
                else:
                    break
            if tmp_count > max_count:
                max_count = tmp_count
                if (int(danmu_sec) - sec_duration / 6) >= 0:
                    max_sec_start = int(int(danmu_sec) - sec_duration / 6)
                else:
                    max_sec_start = 0

        danmu_time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', danmu)[0]
        danmu_time_start = datetime.strptime(danmu_time_start_str, '%H-%M')
        max_time_start = danmu_time_start + timedelta(seconds = int(max_sec_start))
        top_moments.append({'max_count': max_count,
                            'max_sec_start': int(max_sec_start),
                            'sec_duration': sec_duration,
                            'danmu_file': danmu,
                            'max_time_start': max_time_start})
    return top_moments

def make_moment_danmu(moment, danmu_dst):
    danmu_head = '<?xml version="1.0" encoding="UTF-8"?><i>\n'
    danmu_tail = '</i>\n'
    if not os.path.exists(moment['danmu_file']):
        log_print('danmu file {file} not exist.'.format(
            file = moment['danmu_file']), lv=1)
        return
    moment_danmu = [danmu_head]
    with open(moment['danmu_file'], 'r', encoding='utf-8', errors='ignore') as danmu_file:
        for line in danmu_file:
            time = re.findall(r'p="(\d+).', line)
            if time:
                sec = int(time[0])
                if sec < moment['max_sec_start']:
                    continue
                if sec <= moment['max_sec_start'] + moment['sec_duration']:
                    t0 = sec - moment['max_sec_start']
                    moment_line = re.sub(r'p="(\d+).',r'p="{time}.'.format(time = t0), line)
                    moment_danmu.append(moment_line)
                else:
                    break
    moment_danmu.append(danmu_tail)
    makesure_dir(os.path.dirname(danmu_dst))
    with open(danmu_dst, 'w', encoding='utf-8', errors='ignore') as danmu_dst_file:
        for line in moment_danmu:
            danmu_dst_file.write(line)
    return

if __name__ == '__main__':
    danmu_file = os.path.abspath(os.path.join(os.getcwd(), '..', 'tmp', 'zard__13-21_14-40.xml'))
    # danmu_file = os.path.abspath(os.path.join(os.getcwd(), '..', 'tmp', 'zard__15-01_15-01.xml'))
    top3_moments = get_topN_moments(danmu_file, 180, 3)
    print(top3_moments)
    make_moment_danmu(top3_moments[0],
                      os.path.abspath(os.path.join(os.getcwd(), '..', 'tmp', 'moment.xml')))

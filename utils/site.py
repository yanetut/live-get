#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from datetime import datetime, timedelta

from .ffmpeg import make_screenshot, make_moment
from .danmu_analysis import make_moment_danmu, get_topN_moments
from .ffmpeg import make_thumb_video
sys.path.append('..')
from utils.common import log_print, makesure_dir


# make cover from most poplular moment.flv(length 180s) time at 40s
# @moment_dir(path): daily moment dir (has top 3 moments)
# @cover_dir(path): daily cover dir
# @return(Boolean): True or False
def make_site_cover(moment_dir, cover_dir):
    makesure_dir(cover_dir)
    cover_dpi = '1440x810'
    cover_name = 'cover_{dpi}.jpg'.format(dpi = cover_dpi)
    cover_moment_time = 40
    moment_files = os.listdir(moment_dir)
    max_danmu_size = 0
    max_danmu_file = ''
    for mf in moment_files:
        if re.findall(r'\.xml', mf):
            fsize = os.path.getsize(os.path.join(moment_dir, mf))
            if fsize > max_danmu_size:
                max_danmu_size = fsize
                max_danmu_file = mf
    if max_danmu_file:
        max_moment_file = max_danmu_file[:-4] + '.flv'
        src = os.path.join(moment_dir, max_moment_file)
        dst = os.path.join(cover_dir, cover_name)
        ret = make_thumb_video(src, dst, cover_dpi,
                               time = cover_moment_time)
        if ret == 0:
            return True
    return False


# make screenshots from src
# screenshot name format: 'screenshot__day2_00-09.jpg'
# @src(path): video flv src file
# @dst_dir(path): screenshot dir
# @s_day(int): 1 or 2
# @s_type: (string)'oclock' | (int)number of minute
def do_make_site_screenshot(src, dst_dir, s_day = 1, s_type = 'oclock'):
    log_print('do make screenshot')
    src_name = os.path.basename(src)
    time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', src_name)[0]
    time_end_str = re.findall(r'_([-+]?\d+-[-+]?\d+)\.', src_name)[0]
    time_end = datetime.strptime(time_end_str, '%H-%M')
    time_start = datetime.strptime(time_start_str, '%H-%M')
    sec_total = (time_end - time_start).seconds
    if s_type == 'oclock':
        if time_start.minute == 0:
            sec_start = 0
        else:
            sec_start = (60 - time_start.minute) * 60
        sec_delta = 60 * 60
    elif type(s_type) == int:
        sec_start = 0
        sec_delta = s_type * 60
    else:
        log_print('type error.', lv=1)
        return
    log_print('file:{src}.'.format(src = src))
    for sec in range(sec_start, sec_total, sec_delta):
        time = time_start + timedelta(seconds = sec)
        if time.day == 2 or s_day == 2:
            day = 2
        else:
            day = 1
        screenshot_file_name = 'screenshot__day{day}_{time}.jpg'.format(
            day = day,
            time = time.strftime('%H-%M')
        )
        dst = os.path.join(dst_dir, screenshot_file_name)
        make_screenshot(src, dst, sec)


# make site moment from src_dir_list, eg. day1 and day2
# @live_files: live video and danmaku abspath
# @dst_dir(path): screenshot_dir
def make_site_screenshot(live_files, dst_dir):
    log_print('make screenshot %s into %s' % (live_files, dst_dir))
    dst_date = os.path.basename(dst_dir)
    makesure_dir(dst_dir)
    for live_file in live_files:
        if re.match(r'.*\.flv$', live_file):
            live_date = os.path.basename(os.path.dirname(live_file))
            day = 1 if live_date == dst_date else 2
            do_make_site_screenshot(live_file, dst_dir, day)

    # if no screenshot in oclock mode (duration < 60min)
    if not os.listdir(dst_dir):
        for live_file in live_files:
            if re.match(r'.*\.flv$', live_file):
                live_file_name = os.path.basename(live_file)
                s1 = re.findall(r'__(\d+-\d+)_', live_file_name)[0]
                s2 = re.findall(r'_(\d+-\d+)\.flv$', live_file_name)[0]
                t1 = datetime.strptime(s1, '%H-%M')
                t2 = datetime.strptime(s2, '%H-%M')
                delta_minute = int((t2 - t1).seconds / 60 / 2)
                do_make_site_screenshot(live_file, dst_dir, 1,
                                        s_type = delta_minute)

def _get_moment_name(moment, moment_dir):
    live_date = os.path.basename(moment_dir)
    danmu_date = os.path.basename(os.path.dirname(moment['danmu_file']))
    mt = moment['max_time_start']
    if (danmu_date != live_date):
        day = 2
    else:
        day = mt.day
    moment_time = 'day{day}_{time}'.format(
        day = day,
        time = mt.strftime('%H-%M'))
    moment_name = 'moment__{time}'.format(time = moment_time)
    return moment_name

def remove_site_moment(moment, moment_dir):
    log_print('remove moment {danmu}'.format(danmu = moment['danmu_file']))
    moment_name = _get_moment_name(moment, moment_dir)
    moment_flv = os.path.join(moment_dir, moment_name + '.flv')
    moment_danmu = os.path.join(moment_dir, moment_name + '.xml')
    os.remove(moment_flv)
    log_print('remove moment {flv}'.format(flv=moment_flv))
    os.remove(moment_danmu)
    log_print('remove moment {danmu}'.format(danmu=moment_danmu))

# make site moment from moments
# @moments
# @moment_dir(path)
def make_site_moment(moment, moment_dir):
    danmu_file = moment['danmu_file']
    log_print('make moment {danmu}'.format(danmu = moment['danmu_file']))
    flv_name = os.path.basename(danmu_file)[:-4] + '.flv'
    flv_file = os.path.join(os.path.dirname(danmu_file), flv_name)
    moment_name = _get_moment_name(moment, moment_dir)
    moment_flv = os.path.join(moment_dir, moment_name + '.flv')
    moment_danmu = os.path.join(moment_dir, moment_name + '.xml')
    make_moment(flv_file, moment_flv, moment['max_sec_start'],
                moment['sec_duration'])
    make_moment_danmu(moment, moment_danmu)

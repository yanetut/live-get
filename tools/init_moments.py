#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import shutil
import time
from tqdm import tqdm

from ffmpeg import make_moment, make_screenshot
from danmu_analysis import make_moment_danmu, get_topN_moments
from pcs import download
from datetime import datetime, timedelta

# based on danmu_merge dirctory
base_dir = os.path.abspath(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), '..'))
moment_dir = os.path.join(base_dir, 'moment')
screenshot_dir = os.path.join(base_dir, 'screenshot')
danmu_merge_dir = os.path.join(base_dir, 'danmu_merge', 'zard')
download_tmp_dir = os.path.join(base_dir, 'tmp')
log_dir = os.path.join(base_dir, 'log')
# files init
log_file = os.path.join(log_dir, 'screenshot_moments.log')
# remote dirname
remote_base_dir = 'apps/bypy/zard'


def makesure_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok = True)


def log_init(log_file):
    log_f = open(log_file,  'w')
    sys.stdout = log_f
    sys.stderr = log_f


def log_info(str):
    print('[%s] %s' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), str))
    sys.stdout.flush()


def main():
    global log_file
    global base_dir, moment_dir, screenshot_dir, danmu_merge_dir, download_tmp_dir
    global remote_base_dir
    for dir in [moment_dir, screenshot_dir, download_tmp_dir, log_dir]:
        makesure_dir(dir)
    log_init(log_file)
    # sec_duration: moment duration 3 minutes
    # sec_delta: screenshot delta 10 minutes
    sec_duration = 180
    sec_delta = 600
    top_n = 3
    for live_date in tqdm(sorted(os.listdir(danmu_merge_dir))):
        # skip already maked moments & screenshot
        if (os.path.exists(os.path.join(screenshot_dir, live_date)) and
            os.path.exists(os.path.join(moment_dir, live_date))):
            continue
        # get top 3 moments in all danmu_files
        live_path = os.path.join(danmu_merge_dir, live_date)
        danmus = os.listdir(live_path)
        moments = []
        for danmu in danmus:
            danmu_file = os.path.join(live_path, danmu)
            moments += get_topN_moments(danmu_file, sec_duration, top_n)
        max_moments = []
        for i in range(top_n):
            max_moment = moments[0]
            max_count = max_moment['max_count']
            for moment in moments:
                if moment['max_count'] > max_count:
                    max_count = moment['max_count']
                    max_moment = moment
            max_moments.append(max_moment)
            moments.remove(max_moment)
        # download each flv, make moments & screenshot
        danmus = os.listdir(live_path)
        for danmu in danmus:
            # get remote file path
            flv_remote = remote_base_dir
            if re.findall(r'day2__', danmu):
                day1 = datetime.strptime(live_date, '%Y-%m-%d')
                live_date_day2 = (day1 + timedelta(days = 1)).strftime('%Y-%m-%d')
                flv_remote += '/{day}'.format(day = live_date_day2)
                flv_filename = danmu.replace('xml', 'flv').replace('day2__', '')
            else:
                flv_remote += '/{day}'.format(day = live_date)
                flv_filename = danmu.replace('xml', 'flv')
            flv_remote += '/{filename}'.format(filename = flv_filename)
            # download remote file
            flv_local = os.path.join(download_tmp_dir, flv_filename)
            if not os.path.exists(flv_local):
                log_info('download remote: {remote}\nlocal: {local}\n'.format(
                    remote = flv_remote, local = flv_local))
                retry = 4
                for r in range(retry):
                    ret = download(flv_remote, flv_local)
                    log_info('download return: {ret}'.format(
                        ret = ret.returncode))
                    if not ret.returncode:
                        break

            # danmu is moment danmu? make moment & make moment danmu
            for max_moment in max_moments:
                if os.path.basename(max_moment['danmu_file']) == danmu:
                    # make moment & make moment danmu
                    log_info('make moment {danmu}'.format(danmu = danmu))
                    moment_date_dir = os.path.join(moment_dir, live_date)
                    makesure_dir(moment_date_dir)
                    mt = max_moment['max_time_start']
                    if re.findall(r'day2__', danmu):
                        day = 2
                    else:
                        day = mt.day
                    moment_time = 'day{day}_{time}'.format(day = day, time = mt.strftime('%H-%M'))
                    flv_dst = os.path.join(moment_date_dir,
                                           'moment__{moment}.flv'.format(moment = moment_time))
                    make_moment(flv_local, flv_dst, max_moment['max_sec_start'],
                                max_moment['sec_duration'])
                    danmu_dst = os.path.join(moment_date_dir,
                                             'moment__{moment}.xml'.format(moment = moment_time))
                    make_moment_danmu(max_moment, danmu_dst)
            # make screenshots
            danmu_time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', danmu)[0]
            danmu_time_end_str = re.findall(r'_([-+]?\d+-[-+]?\d+)\.', danmu)[0]
            danmu_time_end = datetime.strptime(danmu_time_end_str, '%H-%M')
            danmu_time_start = datetime.strptime(danmu_time_start_str, '%H-%M')
            sec_total = (danmu_time_end - danmu_time_start).seconds
            screenshot_date_dir = os.path.join(screenshot_dir, live_date)
            makesure_dir(screenshot_date_dir)
            log_info('make screenshots {src}'.format(src = flv_local))
            for sec in range(sec_delta, sec_total, sec_delta):
                time = danmu_time_start + timedelta(seconds = sec)
                if time.day == 2 or re.findall(r'day2__', danmu):
                    day = 2
                else:
                    day = 1
                screenshot_time = 'day{day}_{time}'.format(day = day, time = time.strftime('%H-%M'))
                screenshot_dst = os.path.join(screenshot_date_dir, 'screenshot__{time}.jpg'.format(
                    time = screenshot_time))
                make_screenshot(flv_local, screenshot_dst, sec)
            # rm flv file
            if os.path.exists(flv_local):
                os.remove(flv_local)
            else:
                log_info('file {file} download fail.'.format(file = flv_local))

def test():
    tmpdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',  'tmp'))
    flv_src = os.path.join(tmpdir, 'zard__13-21_14-40.flv')
    danmu_src = os.path.join(tmpdir, 'zard__13-21_14-40.xml')
    moments = get_topN_moments(danmu_src, 180, 3)
    for idx, moment in enumerate(moments):
        mt = moment['max_time_start']
        moment_time = 'day{day}_{time}'.format(day = mt.day, time = mt.strftime('%H-%M'))
        flv_dst = os.path.join(tmpdir, 'moment__{moment}.flv'.format(moment = moment_time))
        make_moment(flv_src, flv_dst, moment['max_sec_start'], moment['sec_duration'])
        danmu_dst = os.path.join(tmpdir, 'moment__{moment}.xml'.format(moment = moment_time))
        make_moment_danmu(moment, danmu_dst)

if __name__ == '__main__':
    main()

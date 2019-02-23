#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import time
import shutil
from utils.common import log_print
from utils.common import log_init
from utils.common import makesure_dir
from utils.common import list_only_dir
from utils.ffmpeg import reencode_video
from utils.baiducloud import bypy_delete
from utils.baiducloud import bypy_list

live_id = 'zard'

# Dir and File Settings
dir_home = os.getcwd()
# log dir
dir_log = os.path.join(dir_home, 'log')
log_file = os.path.join(dir_log, 'reencode_%s.log' % (live_id))

dir_reencode = os.path.join(dir_home, 'reencode')
dir_src = os.path.join(dir_reencode, 'src')
dir_dst = os.path.join(dir_reencode, 'zard')

reencode_flag = False
src_empty_flag = False
dst_empty_flag = False

def check_dir_src():
    log_print('check_dir_src')
    global src_empty_flag
    global reencode_flag
    live_dates = os.listdir(dir_src)
    if not live_dates:
        src_empty_flag = True
        return
    src_empty_flag = False
    # find latest file to reencode
    live_dates.reverse()
    reencode_file = None
    reencode_date = None
    for live_date in live_dates:
        date_path = os.path.join(dir_src, live_date)
        files = os.listdir(date_path)
        if not files:
            try:
                os.rmdir(date_path)
                log_print('delete empty folder %s' % date_path)
            except PermissionError:
                log_print('PermissionError %s' % date_path)
            continue
        for file_name in files:
            file_path = os.path.join(date_path, file_name)
            if re.match(r'.*\.xml$', file_name):
                os.remove(file_path)
                log_print('delete danmaku file %s' % file_path)
                continue
            if not re.match(r'.*\.flv$', file_name):
                continue
            # get reencode file
            reencode_file = file_path
            reencode_date = live_date
            break
        if reencode_file:
            break
    # do reencode
    if reencode_file:
        log_print('now start reencode %s' % reencode_file)
        retry_times = 3
        while retry_times > 0:
            retcode = reencode_video(reencode_file, gpu=True)
            # upload
            if retcode == 0:
                reencode_flag = True
                bypy_path = '%s/%s/%s' % (live_id, reencode_date, file_name)
                bypy_delete(bypy_path)
                dir_dst_live_date = os.path.join(dir_dst, reencode_date)
                makesure_dir(dir_dst_live_date)
                shutil.move(reencode_file, 
                    os.path.join(dir_dst_live_date, file_name))
                break
            elif retcode == 1:
                log_print('No need reencode %s' % reencode_file)
                retry_times = 0
                break
            retry_times -= 1
        if retry_times == 0:
            log_print('Give up reencode %s' % reencode_file)
            os.remove(reencode_file)

def check_dir_dst():
    log_print('check_dir_dst')
    global dst_empty_flag
    live_dates = list_only_dir(dir_dst)
    if not live_dates:
        dst_empty_flag = True
        return
    dst_empty_flag = False
    for live_date in live_dates:
        date_path = os.path.join(dir_dst, live_date)
        if not os.path.exists(date_path):
            continue
        files = os.listdir(date_path)
        if not files:
            try:
                os.rmdir(date_path)
                log_print('delete empty folder %s' % date_path)
            except PermissionError:
                log_print('PermissionError %s' % date_path)
            continue
        bypy_path = '%s/%s' % (live_id, live_date)
        remote_files = bypy_list(bypy_path)
        for file_name in files:
            if file_name in remote_files:
                # upload done, rm local file
                bypy_file = '%s/%s' % (bypy_path, file_name)
                log_print('upload %s Done' % bypy_file)
                file_path = os.path.join(date_path, file_name)
                os.remove(file_path)

def main():
    global reencode_flag
    # dir settings
    makesure_dir(dir_log)
    makesure_dir(dir_reencode)
    makesure_dir(dir_src)
    makesure_dir(dir_dst)
    # log file setting
    log_init(log_file)
    while True:
        check_dir_src()
        if not reencode_flag:
            time.sleep(30)
            check_dir_dst()
        else:
            reencode_flag = False
        if src_empty_flag and dst_empty_flag:
            # all reencode finished, shutdown
            os.system('shutdown -s -t 0')

if __name__ == '__main__':
    main()

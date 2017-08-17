#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import os
import psutil
import re
import inspect
from datetime import datetime
from shutil import copyfile

# MIN_VIDEO_SIZE_BYTE = 20MB
MIN_VIDEO_SIZE_BYTE = 20971520
# MIN_XML_SIZE_BYTE = 3KB
MIN_XML_SIZE_BYTE = 3072

def makesure_dir(dirname):
    os.makedirs(dirname, exist_ok = True)

def log_init(log_file):
    log_f = open(log_file,  'w')
    sys.stdout = log_f
    sys.stderr = log_f

def log_backup(log_file):
    log_file_bk_name = '{name}_{time}.{type}'.format(
        name = os.path.basename(log_file)[:-4],
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
        type = os.path.basename(log_file)[-3:]
    )
    log_dir = os.path.dirname(log_file)
    log_bk_file = os.path.join(log_dir, log_file_bk_name)
    copyfile(log_file, log_bk_file)


# @str(string): log message
# @lv(int): log level [0:INFO, 1:ERROR]
def log_print(msg, lv = 0):
    if lv == 1:
        log_lv = 'ERROR'
    else:
        log_lv = 'INFO'
    log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    module = inspect.stack()[1][3]
    msg = '[{log_time}][{log_lv}][{log_module}] {log_msg}'.format(
        log_lv = log_lv,
        log_time = log_time,
        log_msg = msg,
        log_module = module
    )
    print(msg)
    sys.stdout.flush()

def kill_pid(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def rm_small_file(path, regexp = ''):
    if not os.path.exists(path):
        log_print('path not exist: %s' % path)
        return
    filelist = os.listdir(path)

    for f in filelist:
        if regexp and not re.match(regexp, f):
            continue
        file_abs = os.path.join(path, f)
        filesize = os.path.getsize(file_abs)
        log_print('size of %s: %s' % (file_abs, filesize))
        if re.match('.*.(flv|mp4)$', file_abs) and filesize <= MIN_VIDEO_SIZE_BYTE:
            os.remove(file_abs)
            log_print('rm_small_file SUCCESS %s' % f)
        elif re.match('.*.xml$', file_abs) and filesize <= MIN_XML_SIZE_BYTE:
            os.remove(file_abs)
            log_print('rm_small_file SUCCESS %s' % f)

def get_delta_minute(filename):
    time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', filename)[0]
    time_end_str = re.findall(r'_([-+]?\d+-[-+]?\d+)\.', filename)[0]
    time_start = datetime.strptime(time_start_str, '%H-%M')
    time_end = datetime.strptime(time_end_str, '%H-%M')
    time_delta = (time_end - time_start).seconds / 60
    return int(time_delta)

def list_only_dir(dir):
    files = os.listdir(dir)
    only_dirs = [f for f in files if os.path.isdir(os.path.join(dir, f))]
    return only_dirs

def exist_cmd(cmd):
    for cmdpath in os.environ['PATH'].split(';'):
        if os.path.isdir(cmdpath) and cmd in os.listdir(cmdpath):
            return True
    return False

if __name__ == '__main__':
    print(exist_cmd('ffmpeg_g.exe'))

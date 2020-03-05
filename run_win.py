#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import oss2
import sys
import re
import time
import codecs
import shutil
import subprocess
from threading import Thread
from datetime import datetime
from pathlib import PurePosixPath
from api import douyu_opencdn
from utils.common import makesure_dir
from utils.common import kill_pid
from utils.common import list_only_dir
from utils.common import log_init
from utils.common import log_print
from utils.site import make_site_moment
from utils.site import get_topN_moments
from utils.site import remove_site_moment
from utils.site import rename_moment_file
from utils.ffmpeg import to_hls
from utils.ffmpeg import reencode_video
from utils.ffmpeg import flv_to_mp4
from utils.baiducloud import CloudManager
from utils.danmu_analysis import get_moment
from utils.danmu_file_maker import DanMuFileMaker
from tools.convert import covj
from configparser import ConfigParser

# Global Settings
# Live Settings
live_id = 'zard'
live_id_num = '60937'
live_online = False
sleep_sec = 30
live_max_minute = 120
max_moments = []

# Dir and File Settings
dir_home = os.getcwd()
# log dir
dir_log = os.path.join(dir_home, 'log')
log_file = os.path.join(dir_log, 'run_%s.log' % (live_id))
# local dir
dir_local = os.path.join(dir_home, 'local')
dir_live = os.path.join(dir_local, 'live', live_id)
# site dir
dir_site_moment = os.path.join(dir_local, 'site', 'moment')
# local sync dir
dir_cloud = os.path.join(dir_home, 'cloud')
dir_cloud_live = os.path.join(dir_cloud, 'live', live_id)
dir_cloud_site_moment = os.path.join(dir_cloud, 'site', 'moment')

# oss
cfg = ConfigParser()
cfg.read('config/config.ini')
bucket = oss2.Bucket(oss2.Auth(cfg.get('oss', 'key_id'), cfg.get(
    'oss', 'key_secret')), cfg.get('oss', 'endpoint'), cfg.get('oss', 'bucket'))
moment_base = 'moment'


def start_you_get(filename, live_date_dir):
    # downloader output
    downloader_out_file = os.path.join(
        dir_log, 'downloader_%s.out' % (live_id))
    with open(downloader_out_file, 'w+', encoding='utf-8') as downloader_out:
        # downloader you-get
        cmd = ('you-get -o %s -O %s.flv %s%s' % (live_date_dir, filename,
                                                 douyu_opencdn.URL_LIVE_DOUYU, live_id_num))
        you_get_proc = subprocess.Popen(cmd,
                                        stdout=downloader_out,
                                        stderr=downloader_out)
    # 等待you-get成功或错误超时
    with open(downloader_out_file, 'r', encoding='utf-8',
              errors='ignore') as outfile:
        line = outfile.readline()
        line_count = 1
        while (not re.match(r'.*time=.*', line)
                and line_count <= 800
                and you_get_proc.poll() is None):
            time.sleep(0.1)
            line = outfile.readline()
            line_count += 1
        # 判断匹配上还是超时或错误输出
        if line_count > 800 or you_get_proc.poll() is not None:
            # you-get 失败，返回None
            # kill_pid(you_get_proc.pid)
            you_get_proc = None
            log_print('you-get FAILED,total_line: %d' % line_count)
        # you-get正常
        else:
            log_print('you-get SUCCESS,total_line: %d' % line_count)
    return you_get_proc


def wait_record_live():
    date_live = datetime.now().date().isoformat()
    dir_live_date = os.path.join(dir_live, date_live)
    makesure_dir(dir_live_date)
    live_time_start = time.strftime('%H-%M', time.localtime())
    you_get_proc = start_you_get(live_time_start, dir_live_date)
    if you_get_proc is not None:
        live_file = os.path.join(dir_live_date, '%s.flv' % live_time_start)
        # start_record_danmu
        danmu_url = '%s%s' % (douyu_opencdn.URL_LIVE_DOUYU, live_id_num)
        dmfm = DanMuFileMaker(danmu_url, dir_live_date)
        dmfm.start()
        try:
            you_get_proc.wait(live_max_minute * 60)
        except subprocess.TimeoutExpired:
            kill_pid(you_get_proc.pid)
        dmfm.stop()
        # record live offline date and time
        live_time_stop = time.strftime('%H-%M', time.localtime())
        name_format = '%s__%s_%s' % (live_id, live_time_start, live_time_stop)
        log_print('stop record live, name: %s' % name_format)
        # live文件重命名添加结束时间
        ret = False
        try_time = 3
        try_wait = 5
        while not ret and try_time:
            try:
                if os.path.exists(live_file):
                    new_file = os.path.join(os.path.dirname(live_file),
                                            '%s.flv' % name_format)
                    os.rename(live_file, new_file)
                ret = True
            except:
                log_print('rename error and wait', lv=1)
                ret = False
                try_time -= 1
                time.sleep(try_wait)
        danmu_file = os.path.join(dir_live_date, '%s.xml' % live_id_num)
        ret = False
        try_time = 3
        while not ret and try_time:
            try:
                if os.path.exists(danmu_file):
                    new_file = os.path.join(os.path.dirname(danmu_file),
                                            '%s.xml' % name_format)
                    os.rename(danmu_file, new_file)
                ret = True
            except:
                log_print('rename error and wait', lv=1)
                ret = False
                try_time -= 1
                time.sleep(try_wait)
    else:
        time.sleep(4)


def check_live_upload():
    log_print('check live upload')
    dir_list = sorted(list_only_dir(dir_live))
    todo_live_list = []
    if dir_list:
        for dir_name in dir_list:
            ldir = os.path.join(dir_live, dir_name)
            for f in os.listdir(ldir):
                if re.match('^{live_id}__.*$'.format(live_id=live_id), f):
                    todo_live_list.append(os.path.join(ldir, f))
                    log_print('add live file: %s' % os.path.join(ldir, f))
            for live_file in todo_live_list:
                if re.match('.*.flv$', live_file):
                    log_print('reencode live video file: %s' % live_file)
                    reencode_video(live_file, gpu=False)
    return todo_live_list


def check_site_upload():
    global max_moments
    live_dates = sorted(os.listdir(dir_site_moment))
    if live_dates:
        live_date = live_dates[0]
        date_now = datetime.now().date()
        date_live = datetime.strptime(live_date, '%Y-%m-%d').date()
        lives = os.listdir(dir_live)
        if not live_online and date_now > date_live and not lives:
            moment_dir = os.path.join(dir_site_moment, live_date)
            moment_files = os.listdir(moment_dir)
            if not moment_files:
                os.rmdir(moment_dir)
                return
            files = map(lambda val: val[:-4], moment_files)
            fileset = set(files)
            for f in fileset:
                file_mp4 = os.path.join(moment_dir, '%s.mp4' % f)
                file_xml = os.path.join(moment_dir, '%s.xml' % f)
                if not os.path.exists(file_mp4):
                    log_print('%s not exists' % file_mp4, 1)
                    continue
                if not os.path.exists(file_xml):
                    log_print('%s not exists' % file_xml, 1)
                    continue
                # convert hls
                newfile_mp4 = rename_moment_file(file_mp4)
                ret = to_hls(newfile_mp4)
                if not ret:
                    log_print('to hls failed %s, skip json convert' % newfile_mp4, 1)
                    continue
                else:
                    log_print('to hls success %s' % newfile_mp4)
                # convert hls success then convert dm to json
                new_moment_dir = newfile_mp4[:-4]
                newfile_xml = rename_moment_file(file_xml)
                dst_json = os.path.join(new_moment_dir, 'dm.json')
                ret = covj(codecs.open(newfile_xml, 'r', encoding='utf-8'),
                           codecs.open(dst_json, 'w', encoding='utf-8'))
                if not ret:
                    log_print('dm convert failed %s, skip upload' % dst_json, 1)
                    continue
                else:
                    log_print('dm convert success %s' % dst_json)
                # upload dir
                ret = True
                for root, _, files in os.walk(new_moment_dir):
                    for fname in files:
                        dstpath = str(PurePosixPath(
                            moment_base, live_date,
                            os.path.basename(new_moment_dir),
                            os.path.relpath(root, new_moment_dir).replace('\\', '/'),
                            fname))
                        retry_times = 3
                        while retry_times > 0:
                            try:
                                bucket.put_object_from_file(
                                    dstpath, os.path.join(root, fname))
                                break
                            except:
                                err = sys.exc_info()[0]
                                log_print('ERROR: %s' % err, 1)
                                retry_times -= 1
                        if retry_times == 0:
                            ret = False
                if not ret:
                    log_print('upload failed %s, skip delete' % new_moment_dir, 1)
                    break
                else:
                    log_print('upload success %s' % new_moment_dir)
                # all convert && upload success
                os.remove(newfile_mp4)
                os.remove(newfile_xml)
                shutil.rmtree(new_moment_dir)
                log_print('delete success %s' % new_moment_dir)
            moment_files = os.listdir(moment_dir)
            if not moment_files:
                os.rmdir(moment_dir)
                log_print('ALL DONE, delete %s' % moment_dir)
            max_moments = []


def work_record_live():
    global live_online
    while True:
        live_online = douyu_opencdn.is_room_online(live_id_num)
        log_print('live online: %s' % live_online)
        if live_online:
            wait_record_live()
        else:
            time.sleep(sleep_sec)


def work_upload():
    global max_moments
    cloud_manager = CloudManager(live_id, dir_cloud_live)
    # init max_moments
    res = list_only_dir(dir_site_moment)
    if res:
        moment_date = res[0]
        moment_dir = os.path.join(dir_site_moment, moment_date)
        moment_files_name = os.listdir(moment_dir)
        for moment_name in moment_files_name:
            if re.match(r'.*\.xml$', moment_name):
                max_moments.append(get_moment(moment_name, moment_dir))
    while True:
        todo_live_list = check_live_upload()
        if todo_live_list:
            log_print('upload list: %s' % todo_live_list)
            if list_only_dir(dir_site_moment):
                live_date = sorted(list_only_dir(dir_site_moment))[0]
            else:
                live_date = sorted(list_only_dir(dir_live))[0]

            # do some site work
            # moment
            moments = []
            for live_file in todo_live_list:
                if re.match(r'.*\.xml$', live_file):
                    moments += get_topN_moments(live_file, 180, 3)
            # new moments
            new_max_moments = []
            moments += max_moments
            if len(moments) > 3:
                for i in range(3):
                    max_moment = moments[0]
                    max_count = max_moment['max_count']
                    for moment in moments:
                        if moment['max_count'] > max_count:
                            max_count = moment['max_count']
                            max_moment = moment
                    new_max_moments.append(max_moment)
                    moments.remove(max_moment)
            else:
                new_max_moments = moments
            need_delete_moments = [
                m for m in max_moments if not m in new_max_moments]
            need_make_moments = [
                m for m in new_max_moments if not m in max_moments]
            log_print('need_delete_moments: %s' % need_delete_moments)
            log_print('need_make_moments: %s' % need_make_moments)
            moment_dir = os.path.join(dir_site_moment, live_date)
            makesure_dir(moment_dir)
            for moment in need_delete_moments:
                try:
                    remove_site_moment(moment, moment_dir)
                except:
                    log_print('Error in delete moments {moment}'.format(
                        moment=moment['max_time_start']
                    ), lv=1)
            for moment in need_make_moments:
                make_site_moment(moment, moment_dir)
            max_moments = new_max_moments
            # move to cloud dir
            for live_file in todo_live_list:
                todo_date = os.path.basename(os.path.dirname(live_file))
                dir_cloud_live_date = os.path.join(dir_cloud_live, todo_date)
                makesure_dir(dir_cloud_live_date)
                shutil.move(live_file, dir_cloud_live_date)
                cloud_manager.add_cloud(dir_cloud_live_date)
        # rm empty lives dir
        live_dates = list_only_dir(dir_live)
        for live_date in live_dates:
            dir_live_date = os.path.join(dir_live, live_date)
            if not os.listdir(dir_live_date) and not live_online:
                log_print('rmdir %s' % dir_live_date)
                try:
                    os.rmdir(dir_live_date)
                except PermissionError:
                    log_print('PermissionError %s' % dir_live_date)
        cloud_manager.check_upload()
        # live end upload site and danmu
        check_site_upload()
        time.sleep(300)


def main():
    # dir settings
    makesure_dir(dir_log)
    makesure_dir(dir_live)
    makesure_dir(dir_site_moment)
    makesure_dir(dir_cloud_live)
    makesure_dir(dir_cloud_site_moment)
    # log file setting
    log_init(log_file)

    t_record_live = Thread(target=work_record_live)
    t_upload = Thread(target=work_upload)
    t_record_live.start()
    time.sleep(10)
    t_upload.start()


if __name__ == '__main__':
    main()

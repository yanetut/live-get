#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import re
import shutil

sys.path.append("..")
from utils.baiducloud import *
from utils.common import *
from tqdm import tqdm
from datetime import timedelta

live_id = 'zard'
danmu_merge_cloud_root_path = 'danmu_merge'
danmu_merge_local_root_path = os.path.abspath(os.path.join(os.getcwd(), '..', 'danmu_merge', live_id))
live_cloud_root_path = '%s' % live_id
live_date_start = '2017-10-20'

def copy_danmu_files(live_dates):
    global live_cloud_root_path, danmu_merge_cloud_root_path
    patt = re.compile('.*\.xml$')
    # show a smart progress bar with tqdm
    for live_date in tqdm(live_dates):
        live_path = '%s/%s' % (live_cloud_root_path, live_date)
        files = bypy_list(live_path, 'file')
        danmu_files = [f for f in files if patt.match(f)]
        for f in danmu_files:
            f_full_path = '%s/%s' % (live_path, f)
            bypy_copy(f_full_path, '%s/%s' % (danmu_merge_cloud_root_path, f_full_path))

def build_danmu_merge():
    global live_cloud_root_path, danmu_merge_cloud_root_path, live_date_start
    # delete danmu_merge path
    bypy_delete(danmu_merge_cloud_root_path)
    # copy danmu files recursively
    # from live_cloud_root_path to danmu_merge_cloud_root_path
    live_dates = bypy_list(live_cloud_root_path, 'dir')
    format_date = '%Y-%m-%d'
    live_dates = [l for l in live_dates if (
                 datetime.strptime(l, format_date)
                 >= datetime.strptime(live_date_start, format_date))]
    copy_danmu_files(live_dates)

def update_danmu_merge():
    global live_cloud_root_path, danmu_merge_cloud_root_path, live_date_start, live_id
    live_dates = bypy_list(live_cloud_root_path, 'dir')
    format_date = '%Y-%m-%d'
    live_dates = [l for l in live_dates if (
                 datetime.strptime(l, format_date)
                 >= datetime.strptime(live_date_start, format_date))]
    old_live_dates = bypy_list('%s/%s' % (danmu_merge_cloud_root_path, live_id), 'dir')
    update_dates = [d for d in live_dates if not d in old_live_dates]
    copy_danmu_files(update_dates)

# danmu2 - danmu1 < 20 minutes return true, else return false
def is_concat(danmu1, danmu2):
    delta = 1200
    danmu1_time_end_str = re.findall(r'_([-+]?\d+-[-+]?\d+)\.', danmu1)[0]
    danmu2_time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', danmu2)[0]
    danmu1_time_end = datetime.strptime(danmu1_time_end_str, '%H-%M')
    danmu2_time_start = datetime.strptime(danmu2_time_start_str, '%H-%M')
    time_delta = danmu2_time_start - danmu1_time_end
    if time_delta.seconds <= delta:
     return True
    return False

def move_danmu():
    global danmu_merge_local_root_path
    danmu_dates = list_only_dir(danmu_merge_local_root_path)
    moved_danmu_count = 0
    for dm_date in tqdm(danmu_dates):
        dm_date_path = os.path.join(danmu_merge_local_root_path, dm_date)
        dm_files = sorted(os.listdir(dm_date_path))
        if not dm_files:
            shutil.rmtree(dm_date_path)
            continue
        danmu1 = dm_files[-1]
        dm_date_tomorrow = (datetime.strptime(dm_date, '%Y-%m-%d')
                        + timedelta(days=1)).strftime('%Y-%m-%d')
        dm_date_tomorrow_path = os.path.join(danmu_merge_local_root_path,
                                            dm_date_tomorrow)
        if not os.path.exists(dm_date_tomorrow_path):
            continue
        dm_files_tomorrow = sorted(os.listdir(dm_date_tomorrow_path))
        if not dm_files_tomorrow:
            continue
        danmu2 = dm_files_tomorrow[0]
        # danmu2 must between 00-00 -- 04:00
        danmu2_time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', danmu2)[0]
        danmu2_time_start = datetime.strptime(danmu2_time_start_str, '%H-%M')
        time_start = datetime.strptime('00-00', '%H-%M')
        time_end = datetime.strptime('04-00', '%H-%M')
        if not ( danmu2_time_start > time_start and danmu2_time_start < time_end ):
            continue
        if not is_concat(danmu1, danmu2):
            continue
        dm_prev = dm_files_tomorrow.pop(0)
        dm_files_to_move = []
        dm_files_to_move.append(dm_prev)
        for dm in dm_files_tomorrow:
            if is_concat(dm_prev, dm):
                dm_files_to_move.append(dm)
                dm_prev = dm
            else:
                break;
        for dm_move in dm_files_to_move:
            # bug, file name exist, think about rename?
            dm_f = os.path.join(dm_date_tomorrow_path, dm_move)
            dm_f_rename = os.path.join(dm_date_tomorrow_path, 'day2__%s' % dm_move)
            os.rename(dm_f, dm_f_rename)
            shutil.move(dm_f_rename, dm_date_path)
        moved_danmu_count += len(dm_files_to_move)
    print('moved: %d danmu files' % moved_danmu_count)

# merge danmu file in current dir
# make sure danmu_files in order
def merge_danmu_file(danmu_files):
    global live_id
    if len(danmu_files) < 2:
        return
    time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_',  danmu_files[0])[0]
    time_end_str = re.findall(r'_([-+]?\d+-[-+]?\d+)\.',  danmu_files[-1])[0]
    merged_danmu_file = '%s__%s_%s.xml' % (live_id, time_start_str, time_end_str)
    open(merged_danmu_file, 'w+').close()
    danmu_header = '<?xml version="1.0" encoding="UTF-8"?><i>\n'
    danmu_footer = '</i>\n'
    with open(merged_danmu_file, 'w+', encoding='utf-8') as f_merged:
        f_merged.write(danmu_header)
    time_start = datetime.strptime(time_start_str, '%H-%M')
    for danmu_file in danmu_files:
        dm_time_start_str = re.findall(r'__([-+]?\d+-[-+]?\d+)_', danmu_file)[0]
        dm_time_start = datetime.strptime(dm_time_start_str, '%H-%M')
        time_delta = (dm_time_start - time_start).seconds
        with open(danmu_file, 'r', encoding='utf-8', errors='ignore') as danmu_src, open(merged_danmu_file, 'a+', encoding='utf-8') as danmu_dst:
            for line in danmu_src:
                time = re.findall(r'p="(\d+).', line)
                if not time == []:
                    time_all = int(time[0]) + time_delta
                    time_rep = 'p=\"%d.' % time_all
                    line_rep = re.sub(r'p="(\d+).', time_rep, line)
                    danmu_dst.write(line_rep)
    with open(merged_danmu_file, 'a+', encoding='utf-8') as f_merged:
        f_merged.write(danmu_footer)

def merge_danmu():
    global danmu_merge_local_root_path
    danmu_dates = list_only_dir(danmu_merge_local_root_path)
    for dm_date in tqdm(danmu_dates):
        dm_date_path = os.path.join(danmu_merge_local_root_path, dm_date)
        dm_files = sorted(os.listdir(dm_date_path))
        # change working dir
        os.chdir(dm_date_path)
        if not dm_files:
            continue
        # step 1 merge today's danmu files
        today_dm_files = sorted([f for f in dm_files if not re.match(r'^day2.*', f)])
        dm_file_group_to_merge = []
        dm_file_to_merge = []
        today_dm_files_len = len(today_dm_files)
        tomorrow_dm_files = sorted([f for f in dm_files if not f in today_dm_files])
        for key, dm_file in enumerate(today_dm_files):
            if key + 1 < today_dm_files_len:
                if is_concat(dm_file, today_dm_files[key+1]):
                    dm_file_to_merge.append(dm_file)
                    dm_file_to_merge.append(today_dm_files[key+1])
                else:
                    if dm_file_to_merge != []:
                        dm_file_to_merge = sorted(set(dm_file_to_merge))
                        dm_file_group_to_merge.append(dm_file_to_merge)
                        dm_file_to_merge = []
        if dm_file_to_merge != []:
            dm_file_group_to_merge.append(sorted(set(dm_file_to_merge)))
        for dm_files in dm_file_group_to_merge:
            merge_danmu_file(dm_files)
        # delete merged danmu files
        for dm_files in dm_file_group_to_merge:
            for dm_file in dm_files:
                os.remove(os.path.join(dm_date_path, dm_file))
        # step 2 merge tomorrow's danmu files
        if tomorrow_dm_files == []:
            continue
        new_file_list = os.listdir(dm_date_path)
        today_dm_files = sorted([f for f in new_file_list if not re.match(r'^day2.*', f)])
        danmu_files_to_merge = [today_dm_files[-1]] + tomorrow_dm_files
        merge_danmu_file(danmu_files_to_merge)
        # delete merged danmu files
        for dm_file in danmu_files_to_merge:
            os.remove(os.path.join(dm_date_path, dm_file))

def test():
    arr1 = [5,6,7,8,10,22,23,24,33, 34]
    arr1_len = len(arr1)
    seq_group = []
    seq_list = []
    for k,it in enumerate(arr1):
        if k + 1 < arr1_len:
            if is_test(it, arr1[k+1]):
                seq_list.append(it)
                seq_list.append(arr1[k+1])
            else:
                if seq_list != []:
                    seq_list = sorted(set(seq_list))
                    seq_group.append(seq_list)
                    seq_list = []
    if seq_list != []:
        seq_group.append(seq_list)
    print(seq_group)
def is_test(n1,n2):
    if n2 - n1 <= 1:
        return True
    return False

def main():
    #build_danmu_merge()
    #move_danmu()
    #merge_danmu()
    merge_danmu_file(['zard__10-13_15-25.xml', 'zard__15-25_16-14.xml'])

if __name__ == '__main__':
    main()

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os
import argparse
from collections import Counter
from tqdm import tqdm


def get_danmu_user_name(line):
    res = re.findall(r',\d{1,2},([^,]+),[^,]*">', line)
    if res:
        return res[0]
    return ''


def get_danmu_time(line):
    res = re.findall(r'p="(\d+)\.', line)
    if res:
        return int(res[0])
    return -1


def get_users_info(danmu_file, danmu_delta_minute):
    users_info = {}
    danmu_list = []
    with open(danmu_file, 'r', encoding='utf-8', errors='ignore') as dm_file:
        for line in dm_file:
            if re.findall(r',\d{1,2},([^,]+?),[^,]*">', line):
                danmu_list.append(line)
    delta_idx = 0
    danmu_delta_max = (delta_idx + 1) * danmu_delta_minute * 60
    # init all user danmu dict
    danmu_total_time = get_danmu_time(danmu_list[-1])
    delta_idx_total = int(danmu_total_time / (danmu_delta_minute * 60)) + 1
    for danmu in danmu_list:
        user_name = get_danmu_user_name(danmu)
        if not (user_name in users_info):
            users_info[user_name] = [0] * delta_idx_total
    for danmu in danmu_list:
        danmu_time = get_danmu_time(danmu)
        if danmu_time >= danmu_delta_max:
            delta_idx += 1
            danmu_delta_max = (delta_idx + 1) * danmu_delta_minute * 60
        user_name = get_danmu_user_name(danmu)
        users_info[user_name][delta_idx] += 1
    return users_info


def sort_by_stay(users_info):
    users_stay_info = {}
    for user in users_info:
        stay_count = 0
        for dm_count in users_info[user]:
            if not dm_count == 0:
                stay_count += 1
        users_stay_info[user] = stay_count
    sorted_list = sorted(users_stay_info.items(), key = lambda x: x[1],
                         reverse=True)
    return sorted_list


def sort_by_count(users_info):
    users_count_info = {}
    for user in users_info:
        stay_count = 0
        for dm_count in users_info[user]:
            if not dm_count == 0:
                stay_count += dm_count
        users_count_info[user] = stay_count
    sorted_list = sorted(users_count_info.items(), key = lambda x: x[1],
                         reverse=True)
    return sorted_list


def print_sorted_info(users_info):
    pass


def users_info(args):
    if not args.delta:
        delta = 30
    else:
        delta = args.delta
    print(args.file)
    users_info = get_users_info(args.file, delta)
    sorted_stay_info = sort_by_stay(users_info)
    sorted_count_info = sort_by_count(users_info)
    # user count
    print('Total user count: {count}'.format(count = len(users_info)))
    # user danmu count top 50
    print('user danmu count top 50:')
    for i in range(50):
        key = sorted_count_info[i][0]
        v = sorted_count_info[i][1]
        print('{idx}\t{key}: {value}'.format(idx = i + 1, key = key,
                                             value = v))
    # user stay top 50
    delta_max = len(list(users_info.items())[0][1])
    print('user stay top 50(max {max}):'.format(max = delta_max))
    for i in range(50):
        key = sorted_stay_info[i][0]
        v = sorted_stay_info[i][1]
        print('{idx}\t{key}: {value}'.format(idx = i, key = key, value = v))


def get_users_count_info(danmu_file):
    users_count_info = {}
    danmu_list = []
    with open(danmu_file, 'r', encoding='utf-8', errors='ignore') as dm_file:
        for line in dm_file:
            if re.findall(r',\d{1,2},([^,]+?),[^,]*">', line):
                danmu_list.append(line)
    for danmu in danmu_list:
        user_name = get_danmu_user_name(danmu)
        if not (user_name in users_count_info):
            users_count_info[user_name] = 0
        else:
            users_count_info[user_name] += 1
    return users_count_info


def count_info(args):
    users_count_info = Counter({})
    for f in args.count:
        if os.path.exists(f):
            add_count_info = Counter(get_users_count_info(f))
            users_count_info += add_count_info
    # user count
    print('Total user count: {count}'.format(count = len(users_count_info)))
    # sort count
    sorted_count_info = sorted(users_count_info.items(), key = lambda x: x[1],
                               reverse=True)
    for i in range(50):
        key = sorted_count_info[i][0]
        v = sorted_count_info[i][1]
        print('{idx}\t{key}: {value}'.format(idx = i + 1, key = key,
                                             value = v))

    with open('counts.txt', 'w', encoding='utf-8') as count_file:
        idx = 0
        for info in sorted_count_info:
            key = info[0]
            v = info[1]
            count_file.write('{idx}\t{key}: {value}\n'.format(
                idx = idx + 1, key = key, value = v))
            idx += 1

def count_all_info(args):
    users_count_info = Counter({})
    danmu_dir = os.path.join(os.getcwd(), args.countall[0])
    danmu_dirs = os.listdir(danmu_dir)
    danmu_file_list = []
    for dm_dir in danmu_dirs:
        danmu_file_dir = os.path.join(danmu_dir, dm_dir)
        danmu_files = os.listdir(danmu_file_dir)
        for danmu_file in danmu_files:
            dm_file = os.path.join(danmu_file_dir, danmu_file)
            danmu_file_list.append(dm_file)
    for dm_file in tqdm(danmu_file_list):
        add_count_info = Counter(get_users_count_info(dm_file))
        users_count_info += add_count_info
    # user count
    print('Total user count: {count}'.format(count = len(users_count_info)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Get User info from danmaku file.')
    parser.add_argument('-c', '--count', type = str, nargs = '+',
                        help='count help')
    parser.add_argument('-ca', '--countall', type = str, nargs = '+',
                        help='count help')
    parser.add_argument('-f', '--file', type = str, help='danmaku help')
    parser.add_argument('-d', '--delta', type = int, help='delta minute help')
    args = parser.parse_args()

    if args.count:
        count_info(args)
    elif args.file:
        users_info(args)
    elif args.countall:
        count_all_info(args)


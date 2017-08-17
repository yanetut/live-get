#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
from tqdm import tqdm
from xml.sax.saxutils import escape


def regexp_escape(s):
    return re.sub(r"[(){}\[\].*?|^$\\+-]", r"\\\g<0>", s)


def xml_escape_danmu(file_path):
    if not os.path.exists(file_path):
        return
    danmu_head = '<?xml version="1.0" encoding="UTF-8"?><i>\n'
    danmu_tail = '</i>\n'
    danmus = []
    danmus.append(danmu_head)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as dmfile:
        for line in dmfile:
            content = re.findall(r'">([\s\S]*)</d>$', line)
            if content:
                escape_content = escape(content[0])
                try:
                    escape_line = re.sub(r'">([\s\S]+)</d>$',
                                         r'">{content}</d>'
                                         .format(content = escape_content),
                                         line)
                except:
                    escape_line = re.sub(r'">([\s\S]+)</d>$',
                                         r'">{content}</d>'
                                         .format(content = regexp_escape(
                                             escape_content)),
                                         line)
                    print('{date} {name}'.format(
                        date = os.path.dirname(file_path),
                        name = os.path.basename(file_path)))
                    print(line)
                danmus.append(escape_line)
    danmus.append(danmu_tail)
    with open(file_path, 'w', encoding='utf-8', errors='ignore') as dmfile:
        dmfile.writelines(danmus)


def xml_escape_dir(dir):
    files = os.listdir(dir)
    for f in files:
        if re.findall(r'\.xml$', f):
            xml_escape_danmu(os.path.join(dir, f))


if __name__ == '__main__':
    moment_dir = os.path.join(os.path.abspath(os.getcwd()), 'moment')
    moment_dates = os.listdir(moment_dir)
    for moment_date in tqdm(moment_dates):
        xml_escape_dir(os.path.join(moment_dir, moment_date))

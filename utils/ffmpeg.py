#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
from multiprocessing import cpu_count
from .common import exist_cmd
from .common import makesure_dir


sys.path.append('..')
from utils.common import log_print

threads = cpu_count() / 2

def make_screenshot(src, dst, sec_start):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return False
    cmd = ('ffmpeg -ss {sec_start} -i {src} -vframes 1 -q:v 2'
           ' -threads {threads} -y {dst}').format(
        sec_start = sec_start,
        src = src,
        dst = dst,
        threads = threads,
    )
    return subprocess.run(cmd, shell=True)


def make_moment(src, dst, sec_start, sec_duration, gpu=False):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return False
    if not gpu:
        cmd = ('ffmpeg -ss {sec_start} -i {src} -t {sec_duration} -c copy'
               ' -threads {threads} -y {dst}').format(
            sec_start = sec_start,
            sec_duration = sec_duration,
            src = src,
            dst = dst,
            threads = threads,
        )
    else:
        cmd = ('ffmpeg_g -ss {sec_start} -i {src} -t {sec_duration} -c copy'
               ' -y {dst}').format(
            sec_start = sec_start,
            sec_duration = sec_duration,
            src = src,
            dst = dst,
            threads = threads,
        )

    return subprocess.run(cmd, shell=True)


def make_thumb_image(src, dst, dpi):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return False
    cmd = ('ffmpeg -i {src} -s {dpi} -r 1 -vframes 1 -an '
           '-vcodec mjpeg -threads {threads} -y {dst}').format(
               src = src,
               dst = dst,
               dpi = dpi,
               threads = threads,
    )
    return subprocess.run(cmd, shell = True).returncode


def make_thumb_video(src, dst, dpi, time = 0.5):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return False
    cmd = ('ffmpeg -ss {time} -i {src} -s {dpi} -r 1 -vframes 1 -an '
           '-vcodec mjpeg -threads {threads} -y {dst}').format(
               src = src,
               dst = dst,
               dpi = dpi,
               time = time,
               threads = threads,
    )
    return subprocess.run(cmd, shell = True).returncode


def remake_video(src):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return -1
    if not re.findall(r'\.flv$', os.path.basename(src)):
        return -1
    out_name = '{srcname}_out.flv'.format(srcname = os.path.basename(src)[:-4])
    out_file = os.path.join(os.path.dirname(src), out_name)
    cmd = 'ffmpeg -i {src} -t 14400 -codec copy -threads {threads} -y {dst}'.format(
        src = src,
        dst = out_file,
        threads = threads,
    )
    retcode = subprocess.run(cmd, shell = True).returncode
    if retcode == 0:
        os.remove(src)
        os.rename(out_file, src)
    else:
        try:
            os.remove(out_file)
        except:
            pass


# @return type
# 0 -- reencode Success
# 1 -- no need reencode
# 2 -- reencode Failed
def reencode_video(src, gpu=False):
    DEFAULT_SIZE_CP = 536870912    # 512MB

    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return -1
    if not re.findall(r'\.flv$', os.path.basename(src)):
        return -1
    out_name = '{srcname}_out.flv'.format(srcname = os.path.basename(src)[:-4])
    out_file = os.path.join(os.path.dirname(src), out_name)
    if not gpu:
        cmd = 'ffmpeg -i {src} -t 14400 -c:v h264 -c:a copy -vf format=yuv420p -q -1 -b:v 0 -maxrate 4000k -bufsize 4000k -y {dst}'.format(
            src = src,
            dst = out_file,
            threads = threads,
        )
    else:
        cmd = 'ffmpeg_g -i {src} -t 14400 -c:v h264_nvenc -preset hp -c:a copy -vf format=yuv420p -q -1 -b:v 0 -maxrate 4000k -bufsize 4000k -y {dst}'.format(
            src = src,
            dst = out_file,
        )
    retcode = subprocess.run(cmd, shell = True).returncode
    if retcode == 0:
        if os.path.getsize(src) <= os.path.getsize(out_file) + DEFAULT_SIZE_CP:
            # no need to reencode
            os.remove(out_file)
            log_print('reencode %s No Need' % src)
            return 1
        else:
            os.remove(src)
            os.rename(out_file, src)
            log_print('reencode %s Success' % src)
            return 0
    else:
        os.remove(out_file)
        log_print('reencode %s Failed' % src, lv=1)
        return 2


def flv_to_mp4(src):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return False
    dst = src[:-4] + '.mp4'
    if exist_cmd('ffmpeg_g.exe'):
        cmd = ('ffmpeg_g -i {src} -max_muxing_queue_size 1024 -c:v h264 -vf format=yuv420p -q -1 -b:v 0 -maxrate 2000k -y {dst}').format(
            src = src,
            dst = dst
        )
    else:
        cmd = ('ffmpeg -i {src} -max_muxing_queue_size 1024 -c:v h264 -vf format=yuv420p -q -1 -b:v 0 -maxrate 2000k -y {dst}').format(
            src = src,
            dst = dst
        )
    ret1 = subprocess.run(cmd, shell = True).returncode
    src_size = os.path.getsize(src)
    dst_size = os.path.getsize(dst)
    # define error size < 1M
    if dst_size < 1048576:
        os.remove(dst)
        return False
    if ret1 == 0 and dst_size < src_size:
        os.remove(src)
        return True
    else:
        os.remove(dst)
        return False

def to_hls(src, bv_max = 2000, dirname='sd'):
    if not re.match(r'.*\.(flv|mp4)$', src):
        log_print('%s format not match flv|mp4' % src, 1)
        return False
    if not os.path.exists(src):
        log_print('%s not exist.' % src)
        return False
    dst = os.path.join(os.path.dirname(src), os.path.basename(src)[:-4])
    makesure_dir(dst)
    makesure_dir(os.path.join(dst, dirname))
    ffmpeg_cmd = 'ffmpeg'
    if exist_cmd('ffmpeg_g.exe'):
        ffmpeg_cmd = 'ffmpeg_g'
    bv = '-vf format=yuv420p -q -1 -r 30 -c:v h264 -b:v 0 -maxrate %sk \
        -bufsize %sk' % (bv_max, bv_max)
    if bv_max == 'copy':
        bv = '-c:v copy'
    cmd = ('{ffmpeg_cmd} -hide_banner -loglevel panic -i {src} \
        -max_muxing_queue_size 1024 -c:a copy {bv} \
        -hls_time 10 -hls_playlist_type vod -hls_segment_filename \
        {dst}/{dirname}/%03d.ts {dst}/{dirname}/playlist.m3u8').format(
        dirname=dirname,
        bv = bv,
        ffmpeg_cmd = ffmpeg_cmd,
        src = src,
        dst = dst
    )
    ret = subprocess.run(cmd, shell = True).returncode
    if ret == 0:
        log_print('flv_to_hls {src} to hls success'.format(src = src))
        return True
    else:
        log_print('flv_to_hls {src} to hls error'.format(src = src), 1)
        return False

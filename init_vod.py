import sys
import os
import oss2
import re
import shutil
import codecs
from datetime import datetime
from pathlib import PurePosixPath
from utils.common import log_print
from utils.common import log_init
from utils.ffmpeg import to_hls
from utils.site import rename_moment_file
from tools.convert import covj
from configparser import ConfigParser

# log dir
log_path = os.path.join(os.getcwd(), 'log', 'init_vod.log')

# oss
cfg = ConfigParser()
cfg.read('config/config.ini')
bucket = oss2.Bucket(oss2.Auth(cfg.get('oss', 'key_id'), cfg.get(
    'oss', 'key_secret')), cfg.get('oss', 'endpoint'), cfg.get('oss', 'bucket'))
moment_base = 'moment'

moment_dir_root = os.path.abspath('e:/moment')

if __name__ == '__main__':
    log_init(log_path)

    live_dates = os.listdir(moment_dir_root)
    for live_date in live_dates:
        moment_dir = os.path.join(moment_dir_root, live_date)
        moment_files = os.listdir(moment_dir)
        if not moment_files:
            os.rmdir(moment_dir)
            continue
        # mp4 with xml
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
            # size < 50M, codec copy else b:v 2000k
            size_mp4 = os.path.getsize(newfile_mp4)
            bvmax = 'copy'
            if size_mp4 > 50 * 1024 * 1024:
                bvmax = 2000
            ret = to_hls(newfile_mp4, bv_max=bvmax)
            if not ret:
                log_print('to hls failed %s, skip json convert' % newfile_mp4)
                exit(-1)
            else:
                log_print('to hls success %s' % newfile_mp4)
            # convert hls success then convert dm to json
            new_moment_dir = newfile_mp4[:-4]
            newfile_xml = rename_moment_file(file_xml)
            dst_json = os.path.join(new_moment_dir, 'dm.json')
            ret = covj(codecs.open(newfile_xml, 'r', encoding='utf-8'),
                       codecs.open(dst_json, 'w', encoding='utf-8'))
            if not ret:
                log_print('dm convert failed %s, skip upload' % dst_json)
                exit(-1)
            else:
                log_print('dm convert success %s' % dst_json)
            # upload dir
            ret = True
            for root, dirs, files in os.walk(new_moment_dir):
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
                log_print('upload failed %s, skip delete' % new_moment_dir)
                exit(-1)
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

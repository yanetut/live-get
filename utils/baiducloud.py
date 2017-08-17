#!/usr/bin/python3
# -*- coding: utf-8 -*-
###################################
# Upload files to BaiduCloud on Windows
# Dependent on BaiduCloud and bypy
###################################

import os
import shutil
import subprocess
from utils.common import log_print, list_only_dir

test = False

def bypy_copy(path_from, path_to):
    subprocess.call('bypy cp %s %s' % (path_from, path_to),
                    stdout=open(os.devnull, 'wb'))


def bypy_delete(path_delete):
    subprocess.call('bypy delete %s' % path_delete,
                    stdout=open(os.devnull, 'wb'))

# return file list in BaiduCloud bypy dir
# @path root dir default is bypy and separated by '/', eg roomid/livedate
# @type: 'all'|'file'|'dir'
# @return filelist in bypy path dir
def bypy_list(path, list_type = 'all'):
    if list_type == 'file':
        key = '^F\ '
    elif list_type == 'dir':
        key = '^D\ '
    else:
        key = '(^D|^F)\ '

    try:
        ret_bytes = subprocess.check_output(
            'bypy list %s | grep -E "%s"' % (path, key), shell = True)
    except subprocess.CalledProcessError:
        return []

    tmp_list = ret_bytes.decode('utf-8').split('\n')[:-1]
    file_list = []
    for f in tmp_list:
        file_list.append(f.split(' ')[1])
    return(file_list)

class CloudManager():
    def __init__(self, live_id, *cloud_dirs):
        self.bc_list = []
        self.live_id = live_id
        if test:
            self.cloud_path_live = 'test/{id}/'.format(id = self.live_id)
            self.cloud_path_danmu = 'test/danmu/'
            self.cloud_path_site_cover = 'test/site/cover/'
            self.cloud_path_site_screenshot = 'test/site/screenshot/'
            self.cloud_path_site_moment = 'test/site/moment/'
        else:
            self.cloud_path_live = '{id}/'.format(id = self.live_id)
            self.cloud_path_danmu = 'danmu/{id}/'.format( id = self.live_id)
            self.cloud_path_site_cover = 'site/cover/'
            self.cloud_path_site_screenshot = 'site/screenshot/'
            self.cloud_path_site_moment = 'site/moment/'
        for cloud_dir in cloud_dirs:
            date_dirs = list_only_dir(cloud_dir)
            if date_dirs:
                for date_dir in date_dirs:
                    self.add_cloud(os.path.join(cloud_dir, date_dir))

    def uploading(self):
        return not self.bc_list == []
    
    def local_path_list(self):
        local_path_list = []
        for bc in self.bc_list:
            local_path_list.append(bc['local_path'])
        return local_path_list

    def add_cloud(self, local_path):
        if local_path in self.local_path_list():
            return
        path_date = os.path.basename(local_path)
        path_type = os.path.basename(os.path.dirname(local_path))
        cloud_path = ''
        if path_type == self.live_id:
            pre_type = os.path.basename(os.path.dirname(
                                        os.path.dirname(local_path)))
            if pre_type == 'live':
                cloud_path = self.cloud_path_live + path_date
            else:
                cloud_path = self.cloud_path_danmu + path_date
        elif path_type == 'screenshot':
            cloud_path = self.cloud_path_site_screenshot + path_date
        elif path_type == 'moment':
            cloud_path = self.cloud_path_site_moment + path_date
        else:
            cloud_path = self.cloud_path_site_cover + path_date
        bc = {
            'local_path': local_path,
            'cloud_path': cloud_path
        }
        log_print('add_cloud local_path: %s cloud_path: %s' % 
                  (bc['local_path'], bc['cloud_path']))
        self.bc_list.append(bc)

    def check_upload(self):
        log_print('bc_list: %s' % self.bc_list)
        rm_list = []
        for bc in self.bc_list:
            cloud_files = bypy_list(bc['cloud_path'], 'file')
            local_files = os.listdir(bc['local_path'])
            log_print('local_files: %s' % local_files)
            log_print('cloud_files: %s' % cloud_files)
            upload_done = True
            if local_files == []:
                upload_done = True
            else:
                if cloud_files == []:
                    upload_done = False
                else:
                    for f in local_files:
                        if not f in cloud_files:
                            upload_done = False
            if upload_done:
                log_print('live upload is done, remove local_path: %s' %
                        bc['local_path'])
                shutil.rmtree(bc['local_path'])
                rm_list.append(bc)
        for bc in rm_list:
            self.bc_list.remove(bc)

def fn_test():
    ret = bypy_list('zard/2017-08-14', 'file')
    print(ret)

if __name__ == '__main__':
    fn_test()
